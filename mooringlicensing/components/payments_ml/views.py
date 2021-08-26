import datetime
import logging
from decimal import Decimal
from ledger.checkout.utils import calculate_excl_gst
import pytz
import json
from ledger.settings_base import TIME_ZONE
# from ledger.payments.pdf import create_invoice_pdf_bytes
from mooringlicensing.components.main.models import ApplicationType
from mooringlicensing.components.payments_ml.invoice_pdf import create_invoice_pdf_bytes

import dateutil.parser
from django.db import transaction
from django.http import HttpResponse
from django import forms
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import TemplateView
from ledger.basket.models import Basket
from ledger.payments.invoice.models import Invoice
from ledger.payments.utils import update_payments
from oscar.apps.order.models import Order

from mooringlicensing import settings
from mooringlicensing.components.approvals.models import DcvPermit, DcvAdmission, Approval, StickerActionDetail, Sticker
from mooringlicensing.components.compliances.models import Compliance
from mooringlicensing.components.payments_ml.email import send_application_submit_confirmation_email, send_dcv_admission_mail, send_dcv_permit_mail
from mooringlicensing.components.payments_ml.models import ApplicationFee, DcvPermitFee, \
    DcvAdmissionFee, FeeItem, StickerActionFee, FeeItemStickerReplacement
from mooringlicensing.components.payments_ml.utils import checkout, create_fee_lines, set_session_application_invoice, \
    get_session_application_invoice, delete_session_application_invoice, set_session_dcv_permit_invoice, \
    get_session_dcv_permit_invoice, delete_session_dcv_permit_invoice, set_session_dcv_admission_invoice, \
    create_fee_lines_for_dcv_admission, get_session_dcv_admission_invoice, delete_session_dcv_admission_invoice, \
    checkout_existing_invoice, set_session_sticker_action_invoice, get_session_sticker_action_invoice, \
    delete_session_sticker_action_invoice
from mooringlicensing.components.proposals.email import send_application_processed_email
from mooringlicensing.components.proposals.models import Proposal, ProposalUserAction, \
    AuthorisedUserApplication, MooringLicenceApplication, WaitingListApplication, AnnualAdmissionApplication
from mooringlicensing.settings import PROPOSAL_TYPE_AMENDMENT, PROPOSAL_TYPE_RENEWAL, PAYMENT_SYSTEM_PREFIX

logger = logging.getLogger('payment_checkout')


class DcvAdmissionFeeView(TemplateView):

    def get_object(self):
        return get_object_or_404(DcvAdmission, id=self.kwargs['dcv_admission_pk'])

    def post(self, request, *args, **kwargs):
        dcv_admission = self.get_object()
        dcv_admission_fee = DcvAdmissionFee.objects.create(dcv_admission=dcv_admission, created_by=dcv_admission.submitter, payment_type=DcvAdmissionFee.PAYMENT_TYPE_TEMPORARY)

        try:
            with transaction.atomic():
                set_session_dcv_admission_invoice(request.session, dcv_admission_fee)

                lines, db_processes_after_success = create_fee_lines_for_dcv_admission(dcv_admission)

                request.session['db_processes'] = db_processes_after_success
                checkout_response = checkout(
                    request,
                    dcv_admission.submitter,
                    lines,
                    return_url_ns='dcv_admission_fee_success',
                    return_preload_url_ns='dcv_admission_fee_success',
                    invoice_text='DCV Admission Fee',
                )

                logger.info('{} built payment line item {} for DcvAdmission Fee and handing over to payment gateway'.format(dcv_admission.submitter, dcv_admission.id))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating DcvAdmission Fee: {}'.format(e))
            if dcv_admission_fee:
                dcv_admission_fee.delete()
            raise


class DcvPermitFeeView(TemplateView):
    # template_name = 'disturbance/payment/success.html'

    def get_object(self):
        return get_object_or_404(DcvPermit, id=self.kwargs['dcv_permit_pk'])

    def post(self, request, *args, **kwargs):
        dcv_permit = self.get_object()
        created_by = None if request.user.is_anonymous() else request.user
        dcv_permit_fee = DcvPermitFee.objects.create(dcv_permit=dcv_permit, created_by=created_by, payment_type=DcvPermitFee.PAYMENT_TYPE_TEMPORARY)

        try:
            with transaction.atomic():
                set_session_dcv_permit_invoice(request.session, dcv_permit_fee)

                lines, db_processes_after_success = create_fee_lines(dcv_permit)

                request.session['db_processes'] = db_processes_after_success
                checkout_response = checkout(
                    request,
                    dcv_permit.submitter,
                    lines,
                    return_url_ns='dcv_permit_fee_success',
                    return_preload_url_ns='dcv_permit_fee_success',
                    invoice_text='DCV Permit Fee',
                )

                logger.info('{} built payment line item {} for DcvPermit Fee and handing over to payment gateway'.format(request.user, dcv_permit.id))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating DcvPermit Fee: {}'.format(e))
            if dcv_permit_fee:
                dcv_permit_fee.delete()
            raise


class ConfirmationView(TemplateView):
    template_name = 'mooringlicensing/payments_ml/success_submit.html'

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs['proposal_pk'])

    def post(self, request, *args, **kwargs):
        proposal = self.get_object()

        if proposal.application_type.code in (WaitingListApplication.code, AnnualAdmissionApplication.code,):
            self.send_confirmation_mail(proposal, request)
        else:
            pass
            # Confirmation email has been sent in the instance.process_after_submit()

        context = {
            'proposal': proposal,
            'submitter': proposal.submitter,
        }
        return render(request, self.template_name, context)

    @staticmethod
    def send_confirmation_mail(proposal, request):
        # Send invoice
        to_email_addresses = proposal.submitter.email
        email_data = send_application_submit_confirmation_email(proposal, [to_email_addresses, ])

        # Add comms log
        # TODO: Add comms log
        # email_data['approval'] = u'{}'.format(dcv_permit_fee.approval.id)
        # serializer = ApprovalLogEntrySerializer(data=email_data)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()


class ApplicationFeeExistingView(TemplateView):
    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs['proposal_pk'])

    def get(self, request, *args, **kwargs):
        proposal = self.get_object()
        application_fee = proposal.application_fees.first()

        try:
            with transaction.atomic():
                set_session_application_invoice(request.session, application_fee)
                invoice = Invoice.objects.get(reference=application_fee.invoice_reference)

                request.session['db_processes'] = {'payment_for_existing_invoice': True}
                checkout_response = checkout_existing_invoice(
                    request,
                    invoice,
                    return_url_ns='fee_success',
                )

                logger.info('{} built payment line item {} for Application Fee and handing over to payment gateway'.format(
                    'User {} with id {}'.format(
                        request.user.get_full_name(), request.user.id
                    ), application_fee.proposal.lodgement_number
                ))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating Application Fee: {}'.format(e))
            raise


class StickerReplacementFeeView(TemplateView):
    def get_object(self):
        if 'approval_pk' in self.kwargs:
            return get_object_or_404(Approval, id=self.kwargs['approval_pk'])
        elif 'sticker_id' in self.kwargs:
            return get_object_or_404(Sticker, id=self.kwargs['sticker_id'])
        else:
            # Should not reach here
            pass

    def post(self, request, *args, **kwargs):
        # approval = self.get_object()
        data = request.POST.get('data')
        data = json.loads(data)
        ids = data['sticker_action_detail_ids']

        # 1. Validate data
        # raise forms.ValidationError('Validation error')

        # 2. Store detais in the session
        sticker_action_fee = StickerActionFee.objects.create(created_by=request.user, payment_type=StickerActionFee.PAYMENT_TYPE_TEMPORARY)
        current_datetime = datetime.datetime.now(pytz.timezone(TIME_ZONE))

        try:
            with transaction.atomic():
                sticker_action_details = StickerActionDetail.objects.filter(id__in=ids)
                sticker_action_details.update(sticker_action_fee=sticker_action_fee)

                set_session_sticker_action_invoice(request.session, sticker_action_fee)

                # lines, db_processes_after_success = create_fee_lines(proposal)
                target_datetime_str = current_datetime.astimezone(pytz.timezone(TIME_ZONE)).strftime('%d/%m/%Y %I:%M %p')
                application_type = ApplicationType.objects.get(code=settings.APPLICATION_TYPE_REPLACEMENT_STICKER['code'])
                fee_item = FeeItemStickerReplacement.get_fee_item_by_date(current_datetime.date())

                lines = []
                for sticker_action_detail in sticker_action_details:
                    line = {
                        'ledger_description': 'Sticker Replacement Fee, stickker: {} @{}'.format(sticker_action_detail.sticker, target_datetime_str),
                        'oracle_code': application_type.get_oracle_code_by_date(current_datetime.date()),
                        'price_incl_tax': fee_item.amount,
                        'price_excl_tax': calculate_excl_gst(fee_item.amount) if fee_item.incur_gst else fee_item.amount,
                        'quantity': 1,
                    }
                    lines.append(line)

                # request.session['db_processes'] = db_processes_after_success
                checkout_response = checkout(
                    request,
                    request.user,
                    lines,
                    return_url_ns='sticker_replacement_fee_success',
                    return_preload_url_ns='sticker_replacement_fee_success',
                    invoice_text='{}'.format(application_type.description),
                )

                logger.info('{} built payment line item(s) {} for Sticker Replacement Fee and handing over to payment gateway'.format('User {} with id {}'.format(request.user.get_full_name(), request.user.id), sticker_action_fee))
                return checkout_response

        except Exception as e:
            logger.error('Error handling StickerActionFee: {}'.format(e))
            if sticker_action_fee:
                sticker_action_fee.delete()
            raise


        # 3. Once successfully paid, update DB from the data stored in the DB

        # data['sticker'] = sticker.id
        # data['action'] = 'Record returned'
        # data['user'] = request.user.id
        # serializer = StickerActionDetailSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # details = serializer.save()


class StickerReplacementFeeSuccessView(TemplateView):
    template_name = 'mooringlicensing/payments_ml/success_sticker_action_fee.html'
    LAST_STICKER_ACTION_FEE_ID = 'mooringlicensing_last_dcv_admission_invoice'

    def get(self, request, *args, **kwargs):

        try:
            print('1')
            sticker_action_fee = get_session_sticker_action_invoice(request.session)  # This raises an exception when accessed 2nd time?
            print('2')
            sticker_action_details = sticker_action_fee.sticker_action_details

            if self.request.user.is_authenticated():
                owner = request.user
            else:
                owner = sticker_action_details.first().sticker.approval.submitter
            basket = Basket.objects.filter(status='Submitted', owner=owner).order_by('-id')[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)

            sticker_action_fee.invoice_reference = invoice.reference
            sticker_action_fee.save()

            if sticker_action_fee.payment_type == StickerActionFee.PAYMENT_TYPE_TEMPORARY:
                print('3')
                try:
                    inv = Invoice.objects.get(reference=invoice.reference)
                    order = Order.objects.get(number=inv.order_number)
                    order.user = request.user
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error('{} tried paying an application fee with an incorrect invoice'.format(
                        'User {} with id {}'.format(owner.get_full_name(), owner.id)
                    ))
                    return redirect('external')
                if inv.system not in [PAYMENT_SYSTEM_PREFIX,]:
                    logger.error('{} tried paying an application fee with an invoice from another system with reference number {}'.format(
                        'User {} with id {}'.format(owner.get_full_name(), owner.id),
                        inv.reference
                    ))
                    return redirect('external')

                # if fee_inv:
                sticker_action_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                sticker_action_fee.expiry_time = None
                update_payments(invoice.reference)

                for sticker_action_detail in sticker_action_details.all():
                    new_sticker = sticker_action_detail.sticker.request_replacement(Sticker.STICKER_STATUS_LOST)

                sticker_action_fee.save()
                request.session[self.LAST_STICKER_ACTION_FEE_ID] = sticker_action_fee.id
                delete_session_sticker_action_invoice(request.session)  # This leads to raise an exception at the get_session_sticker_action_invoice() above

                # TODO: Email???

                context = {
                    'submitter': owner,
                    'fee_invoice': sticker_action_fee,
                }
                print('render1')
                return render(request, self.template_name, context)

        except Exception as e:
            print('4')
            if (self.LAST_STICKER_ACTION_FEE_ID in request.session) and StickerActionFee.objects.filter(id=request.session[self.LAST_STICKER_ACTION_FEE_ID]).exists():
                sticker_action_fee = StickerActionFee.objects.get(id=request.session[self.LAST_STICKER_ACTION_FEE_ID])
                owner = sticker_action_fee.sticker_action_details.first().sticker.approval.submitter
            else:
                return redirect('home')

            context = {
                'submitter': owner,
                'fee_invoice': sticker_action_fee,
            }
            print('render2')
            return render(request, self.template_name, context)


class ApplicationFeeView(TemplateView):
    # template_name = 'disturbance/payment/success.html'

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs['proposal_pk'])

    def post(self, request, *args, **kwargs):
        proposal = self.get_object()
        application_fee = ApplicationFee.objects.create(proposal=proposal, created_by=request.user, payment_type=ApplicationFee.PAYMENT_TYPE_TEMPORARY)

        try:
            with transaction.atomic():
                set_session_application_invoice(request.session, application_fee)

                lines, db_processes_after_success = create_fee_lines(proposal)

                request.session['db_processes'] = db_processes_after_success
                checkout_response = checkout(
                    request,
                    proposal.submitter,
                    lines,
                    return_url_ns='fee_success',
                    return_preload_url_ns='fee_success',
                    invoice_text='{} ({})'.format(proposal.application_type.description, proposal.proposal_type.description),
                )

                logger.info('{} built payment line item {} for Application Fee and handing over to payment gateway'.format('User {} with id {}'.format(proposal.submitter.get_full_name(),proposal.submitter.id), proposal.id))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating Application Fee: {}'.format(e))
            if application_fee:
                application_fee.delete()
            raise


class DcvAdmissionFeeSuccessView(TemplateView):
    template_name = 'mooringlicensing/payments_ml/success_dcv_admission_fee.html'
    LAST_DCV_ADMISSION_FEE_ID = 'mooringlicensing_last_dcv_admission_invoice'

    def get(self, request, *args, **kwargs):
        proposal = None
        submitter = None
        invoice = None

        try:
            dcv_admission_fee = get_session_dcv_admission_invoice(request.session)  # This raises an exception when accessed 2nd time?

            # Retrieve db processes stored when calculating the fee, and delete the session
            db_operations = request.session['db_processes']
            del request.session['db_processes']

            dcv_admission = dcv_admission_fee.dcv_admission
            # recipient = dcv_permit.applicant_email
            submitter = dcv_admission.submitter

            if self.request.user.is_authenticated():
                basket = Basket.objects.filter(status='Submitted', owner=request.user).order_by('-id')[:1]
            else:
                basket = Basket.objects.filter(status='Submitted', owner=dcv_admission.submitter).order_by('-id')[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)
            invoice_ref = invoice.reference

            # fee_constructor = FeeConstructor.objects.get(id=db_operations['fee_constructor_id'])

            # Update the application_fee object
            dcv_admission_fee.invoice_reference = invoice_ref
            # dcv_admission_fee.fee_constructor = fee_constructor
            dcv_admission_fee.save()

            if dcv_admission_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=inv.order_number)
                    order.user = submitter
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error('{} tried paying an dcv_admission fee with an incorrect invoice'.format('User {} with id {}'.format(dcv_admission.submitter.get_full_name(), dcv_admission.submitter.id) if dcv_admission.submitter else 'An anonymous user'))
                    return redirect('external-dcv_admission-detail', args=(dcv_admission.id,))
                if inv.system not in [PAYMENT_SYSTEM_PREFIX,]:
                # if inv.system != fee_constructor.application_type.oracle_code:
                    logger.error('{} tried paying an dcv_admission fee with an invoice from another system with reference number {}'.format('User {} with id {}'.format(dcv_admission.submitter.get_full_name(), dcv_admission.submitter.id) if dcv_admission.submitter else 'An anonymous user',inv.reference))
                    return redirect('external-dcv_admission-detail', args=(dcv_admission.id,))

                # if fee_inv:
                dcv_admission_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                dcv_admission_fee.expiry_time = None
                update_payments(invoice_ref)

                if dcv_admission and invoice.payment_status in ('paid', 'over_paid',):
                    self.adjust_db_operations(dcv_admission, db_operations)
                    dcv_admission.generate_dcv_admission_doc()
                    # proposal_submit(proposal, request)
                else:
                    logger.error('Invoice payment status is {}'.format(invoice.payment_status))
                    raise

                dcv_admission_fee.save()
                request.session[self.LAST_DCV_ADMISSION_FEE_ID] = dcv_admission_fee.id
                delete_session_dcv_admission_invoice(request.session)

                # DcvAdmissionFeeSuccessView.send_invoice_mail(dcv_admission, invoice, request)
                email_data = send_dcv_admission_mail(dcv_admission, invoice, request)
                # send_application_fee_invoice_apiary_email_notification(request, proposal, invoice, recipients=[recipient])
                #send_application_fee_confirmation_apiary_email_notification(request, application_fee, invoice, recipients=[recipient])
                context = {
                    'dcv_admission': dcv_admission,
                    'submitter': submitter,
                    'fee_invoice': dcv_admission_fee,
                }
                return render(request, self.template_name, context)

        except Exception as e:
            if (self.LAST_DCV_ADMISSION_FEE_ID in request.session) and DcvAdmissionFee.objects.filter(id=request.session[self.LAST_DCV_ADMISSION_FEE_ID]).exists():
                dcv_admission_fee = DcvAdmissionFee.objects.get(id=request.session[self.LAST_DCV_ADMISSION_FEE_ID])
                dcv_admission = dcv_admission_fee.dcv_admission
                submitter = dcv_admission.submitter

            else:
                return redirect('home')

        context = {
            'dcv_admission': dcv_admission,
            'submitter': submitter,
            'fee_invoice': dcv_admission_fee,
        }
        return render(request, self.template_name, context)

    @staticmethod
    def adjust_db_operations(dcv_admission, db_operations):
        dcv_admission.lodgement_datetime = dateutil.parser.parse(db_operations['datetime_for_calculating_fee'])
        dcv_admission.save()


class DcvPermitFeeSuccessView(TemplateView):
    template_name = 'mooringlicensing/payments_ml/success_dcv_permit_fee.html'
    LAST_DCV_PERMIT_FEE_ID = 'mooringlicensing_last_dcv_permit_invoice'

    def get(self, request, *args, **kwargs):
        proposal = None
        submitter = None
        invoice = None

        try:
            dcv_permit_fee = get_session_dcv_permit_invoice(request.session)  # This raises an exception when accessed 2nd time?

            # Retrieve db processes stored when calculating the fee, and delete the session
            db_operations = request.session['db_processes']
            del request.session['db_processes']

            dcv_permit = dcv_permit_fee.dcv_permit
            # recipient = dcv_permit.applicant_email
            submitter = dcv_permit.submitter

            if self.request.user.is_authenticated():
                basket = Basket.objects.filter(status='Submitted', owner=request.user).order_by('-id')[:1]
            else:
                basket = Basket.objects.filter(status='Submitted', owner=dcv_permit.submitter).order_by('-id')[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)
            invoice_ref = invoice.reference

            # fee_constructor = FeeConstructor.objects.get(id=db_operations['fee_constructor_id'])
            fee_item = FeeItem.objects.get(id=db_operations['fee_item_id'])
            try:
                fee_item_additional = FeeItem.objects.get(id=db_operations['fee_item_additional_id'])
            except:
                fee_item_additional = None

            # Update the application_fee object
            dcv_permit_fee.invoice_reference = invoice_ref
            dcv_permit_fee.save()
            dcv_permit_fee.fee_items.add(fee_item)
            if fee_item_additional:
                dcv_permit_fee.fee_items.add(fee_item_additional)

            if dcv_permit_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=inv.order_number)
                    order.user = request.user
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error('{} tried paying an dcv_permit fee with an incorrect invoice'.format('User {} with id {}'.format(dcv_permit.submitter.get_full_name(), dcv_permit.submitter.id) if dcv_permit.submitter else 'An anonymous user'))
                    return redirect('external-dcv_permit-detail', args=(dcv_permit.id,))
                # if inv.system not in ['0517']:
                if inv.system not in [PAYMENT_SYSTEM_PREFIX,]:
                    logger.error('{} tried paying an dcv_permit fee with an invoice from another system with reference number {}'.format('User {} with id {}'.format(dcv_permit.submitter.get_full_name(), dcv_permit.submitter.id) if dcv_permit.submitter else 'An anonymous user',inv.reference))
                    return redirect('external-dcv_permit-detail', args=(dcv_permit.id,))

                # if fee_inv:
                dcv_permit_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                dcv_permit_fee.expiry_time = None
                update_payments(invoice_ref)

                if dcv_permit and invoice.payment_status in ('paid', 'over_paid',):
                    self.adjust_db_operations(dcv_permit, db_operations)
                    dcv_permit.generate_dcv_permit_doc()
                    # proposal_submit(proposal, request)
                else:
                    logger.error('Invoice payment status is {}'.format(invoice.payment_status))
                    raise

                dcv_permit_fee.save()
                request.session[self.LAST_DCV_PERMIT_FEE_ID] = dcv_permit_fee.id
                delete_session_dcv_permit_invoice(request.session)

                # DcvPermitFeeSuccessView.send_invoice_mail(dcv_permit, invoice, request)
                # DcvPermitFeeSuccessView.send_notification_mail(dcv_permit, invoice, request)

                send_dcv_permit_mail(dcv_permit, invoice, request)

                context = {
                    'dcv_permit': dcv_permit,
                    'submitter': submitter,
                    'fee_invoice': dcv_permit_fee,
                }
                return render(request, self.template_name, context)

        except Exception as e:
            print('in ApplicationFeeSuccessView.get() Exception')
            print(e)
            if (self.LAST_DCV_PERMIT_FEE_ID in request.session) and DcvPermitFee.objects.filter(id=request.session[self.LAST_DCV_PERMIT_FEE_ID]).exists():
                dcv_permit_fee = DcvPermitFee.objects.get(id=request.session[self.LAST_DCV_PERMIT_FEE_ID])
                dcv_permit = dcv_permit_fee.dcv_permit
                submitter = dcv_permit.submitter

            else:
                return redirect('home')

        context = {
            'dcv_permit': dcv_permit,
            'submitter': submitter,
            'fee_invoice': dcv_permit_fee,
        }
        return render(request, self.template_name, context)

    @staticmethod
    def adjust_db_operations(dcv_permit, db_operations):
        dcv_permit.start_date = datetime.datetime.strptime(db_operations['season_start_date'], '%Y-%m-%d').date()
        dcv_permit.end_date = datetime.datetime.strptime(db_operations['season_end_date'], '%Y-%m-%d').date()
        dcv_permit.lodgement_datetime = dateutil.parser.parse(db_operations['datetime_for_calculating_fee'])
        dcv_permit.save()


class ApplicationFeeSuccessView(TemplateView):
    template_name = 'mooringlicensing/payments_ml/success_application_fee.html'
    LAST_APPLICATION_FEE_ID = 'mooringlicensing_last_app_invoice'

    def get(self, request, *args, **kwargs):
        print('in ApplicationFeeSuccessView.get()')

        proposal = None
        submitter = None
        invoice = None

        try:
            application_fee = get_session_application_invoice(request.session)  # This raises an exception when accessed 2nd time?

            # Retrieve db processes stored when calculating the fee, and delete the session
            db_operations = request.session['db_processes']
            del request.session['db_processes']

            proposal = application_fee.proposal
            recipient = proposal.applicant_email
            submitter = proposal.submitter

            if self.request.user.is_authenticated():
                basket = Basket.objects.filter(status='Submitted', owner=request.user).order_by('-id')[:1]
            else:
                basket = Basket.objects.filter(status='Submitted', owner=proposal.submitter).order_by('-id')[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)
            invoice_ref = invoice.reference

            # Update the application_fee object
            # For the AUA and MLA, the application_fee already has relations to fee_item(s) created when creating lines.
            # In that case, there are no 'fee_item_id' and/or 'fee_item_additional_id' keys in the db_operations
            if 'fee_item_id' in db_operations:
                fee_items = FeeItem.objects.filter(id=db_operations['fee_item_id'])
                if fee_items:
                    application_fee.fee_items.add(fee_items.first())
            if 'fee_item_additional_id' in db_operations:
                fee_item_additionals = FeeItem.objects.filter(id=db_operations['fee_item_additional_id'])
                if fee_item_additionals:
                    application_fee.fee_items.add(fee_item_additionals.first())
            application_fee.invoice_reference = invoice_ref
            application_fee.save()

            if application_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=inv.order_number)
                    order.user = request.user
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error('{} tried paying an application fee with an incorrect invoice'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user'))
                    return redirect('external-proposal-detail', args=(proposal.id,))
                if inv.system not in [PAYMENT_SYSTEM_PREFIX,]:
                    logger.error('{} tried paying an application fee with an invoice from another system with reference number {}'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user',inv.reference))
                    return redirect('external-proposal-detail', args=(proposal.id,))

                # if fee_inv:
                application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                application_fee.expiry_time = None
                update_payments(invoice_ref)

                if proposal and invoice.payment_status in ('paid', 'over_paid',):
                    proposal.process_after_payment_success(request)
                    self.adjust_db_operations(db_operations)

                    if proposal.application_type.code in (AuthorisedUserApplication.code, MooringLicenceApplication.code):
                        # For AUA or MLA, as payment has been done, create approval
                        # if proposal.proposal_type == PROPOSAL_TYPE_RENEWAL:
                        #     # TODO implemenmt (refer to Proposal.final_approval_for_AUA_MLA)
                        #     pass
                        # elif proposal.proposal_type == PROPOSAL_TYPE_AMENDMENT:
                        #     # TODO implemenmt (refer to Proposal.final_approval_for_AUA_MLA)
                        #     pass
                        # else:
                        #     # approval, created = proposal.create_approval(current_datetime=datetime.datetime.now(pytz.timezone(TIME_ZONE)))
                        #     approval, created = proposal.update_or_create_approval(datetime.datetime.now(pytz.timezone(TIME_ZONE)), request)

                        approval, created = proposal.update_or_create_approval(datetime.datetime.now(pytz.timezone(TIME_ZONE)), request)

                        if created:
                            if proposal.proposal_type == PROPOSAL_TYPE_AMENDMENT:
                                # TODO implemenmt (refer to Proposal.final_approval_for_AUA_MLA)
                                pass
                            # Log creation
                            # Generate the document
                            approval.generate_doc(request.user)
                            proposal.generate_compliances(approval, request)
                            # send the doc and log in approval and org
                        else:
                            # Generate the document
                            approval.generate_doc(request.user)

                            # Delete the future compliances if Approval is reissued and generate the compliances again.
                            approval_compliances = Compliance.objects.filter(approval=approval, proposal=proposal, processing_status='future')
                            for compliance in approval_compliances:
                                compliance.delete()

                            proposal.generate_compliances(approval, request)

                            # Log proposal action
                            proposal.log_user_action(ProposalUserAction.ACTION_UPDATE_APPROVAL_.format(proposal.id), request)

                            # Log entry for organisation
                            applicant_field = getattr(proposal, proposal.applicant_field)
                            applicant_field.log_user_action(ProposalUserAction.ACTION_UPDATE_APPROVAL_.format(proposal.id), request)

                        proposal.approval = approval

                        # send Proposal approval email with attachment
                        send_application_processed_email(proposal, 'approved', True, request)
                        proposal.save(version_comment='Final Approval: {}'.format(proposal.approval.lodgement_number))
                        proposal.approval.documents.all().update(can_delete=False)

                else:
                    logger.error('Invoice payment status is {}'.format(invoice.payment_status))
                    raise

                application_fee.save()
                request.session[self.LAST_APPLICATION_FEE_ID] = application_fee.id
                delete_session_application_invoice(request.session)

                # send_application_fee_invoice_apiary_email_notification(request, proposal, invoice, recipients=[recipient])
                #send_application_fee_confirmation_apiary_email_notification(request, application_fee, invoice, recipients=[recipient])
                context = {
                    'proposal': proposal,
                    'submitter': submitter,
                    'fee_invoice': application_fee,
                }
                return render(request, self.template_name, context)

        except Exception as e:
            print('in ApplicationFeeSuccessView.get() Exception')
            print(e)
            if (self.LAST_APPLICATION_FEE_ID in request.session) and ApplicationFee.objects.filter(id=request.session[self.LAST_APPLICATION_FEE_ID]).exists():
                application_fee = ApplicationFee.objects.get(id=request.session[self.LAST_APPLICATION_FEE_ID])
                proposal = application_fee.proposal
                submitter = proposal.submitter
                if type(proposal.child_obj) in [WaitingListApplication, AnnualAdmissionApplication]:
                    #proposal.child_obj.auto_approve(request)
                    proposal.auto_approve(request)

            else:
                return redirect('home')

        context = {
            'proposal': proposal,
            'submitter': submitter,
            'fee_invoice': application_fee,
        }
        return render(request, self.template_name, context)

    @staticmethod
    def adjust_db_operations(db_operations):
        print(db_operations)
        return


class DcvAdmissionPDFView(View):
    def get(self, request, *args, **kwargs):
        try:
            dcv_admission = get_object_or_404(DcvAdmission, id=self.kwargs['id'])
            response = HttpResponse(content_type='application/pdf')
            if dcv_admission.admissions.count() < 1:
                logger.warn('DcvAdmission: {} does not have any admission document.'.format(dcv_admission))
                return response
            elif dcv_admission.admissions.count() == 1:
                response.write(dcv_admission.admissions.first()._file.read())
                return response
            else:
                logger.warn('DcvAdmission: {} has more than one admissions.'.format(dcv_admission))
                return response
        except DcvAdmission.DoesNotExist:
            raise
        except Exception as e:
            logger.error('Error accessing the DcvAdmission :{}'.format(e))
            raise


class DcvPermitPDFView(View):
    def get(self, request, *args, **kwargs):
        try:
            dcv_permit = get_object_or_404(DcvPermit, id=self.kwargs['id'])
            response = HttpResponse(content_type='application/pdf')
            if dcv_permit.permits.count() < 1:
                logger.warn('DcvPermit: {} does not have any permit document.'.format(dcv_permit))
                return response
            elif dcv_permit.permits.count() == 1:
                response.write(dcv_permit.permits.first()._file.read())
                return response
            else:
                logger.warn('DcvPermit: {} has more than one permits.'.format(dcv_permit))
                return response
        except DcvPermit.DoesNotExist:
            raise
        except Exception as e:
            logger.error('Error accessing the DcvPermit :{}'.format(e))
            raise


class InvoicePDFView(View):
    def get(self, request, *args, **kwargs):
        try:
            invoice = get_object_or_404(Invoice, reference=self.kwargs['reference'])
            # url_var = apiary_url(request)

            # Assume the invoice has been issued for the application(proposal)
            # proposal = Proposal.objects.get(fee_invoice_reference=invoice.reference)
            # proposal = Proposal.objects.get(invoice_references__contains=[invoice.reference])
            # application_fee = ApplicationFee.objects.get(invoice_reference=invoice.reference)
            # proposal = application_fee.proposal

            response = HttpResponse(content_type='application/pdf')
            # response.write(create_invoice_pdf_bytes('invoice.pdf', invoice, url_var, proposal))
            response.write(create_invoice_pdf_bytes('invoice.pdf', invoice,))
            return response

            # if proposal.relevant_applicant_type == 'organisation':
            #     organisation = proposal.applicant.organisation.organisation_set.all()[0]
            #     if self.check_owner(organisation):
            #         response = HttpResponse(content_type='application/pdf')
            #         response.write(create_invoice_pdf_bytes('invoice.pdf', invoice, url_var, proposal))
            #         return response
            #     raise PermissionDenied
            # else:
            #     response = HttpResponse(content_type='application/pdf')
            #     response.write(create_invoice_pdf_bytes('invoice.pdf', invoice, url_var, proposal))
            #     return response
        # except Proposal.DoesNotExist:
        #     # The invoice might be issued for the annual site fee
        #     # annual_rental_fee = AnnualRentalFee.objects.get(invoice_reference=invoice.reference)
        #     # approval = annual_rental_fee.approval
        #     response = HttpResponse(content_type='application/pdf')
        #     # response.write(create_invoice_pdf_bytes('invoice.pdf', invoice, url_var, None))
        #     response.write(create_invoice_pdf_bytes('invoice.pdf', invoice,))
        #     return response
        except Invoice.DoesNotExist:
            raise
        except Exception as e:
            logger.error('Error accessing the Invoice :{}'.format(e))
            raise

    def get_object(self):
        return get_object_or_404(Invoice, reference=self.kwargs['reference'])

    # def check_owner(self, organisation):
    #     return is_in_organisation_contacts(self.request, organisation) or is_internal(self.request) or self.request.user.is_superuser
