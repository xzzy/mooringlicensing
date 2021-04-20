import datetime
import logging

import dateutil.parser
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.views.generic import TemplateView
from ledger.basket.models import Basket
from ledger.payments.invoice.models import Invoice
from ledger.payments.pdf import create_invoice_pdf_bytes
from ledger.payments.utils import update_payments
from oscar.apps.order.models import Order

from mooringlicensing.components.approvals.models import DcvPermit
from mooringlicensing.components.payments_ml.email import send_dcv_permit_fee_invoice
from mooringlicensing.components.payments_ml.models import ApplicationFee, FeeConstructor, DcvPermitFee
from mooringlicensing.components.payments_ml.utils import checkout, create_fee_lines, set_session_application_invoice, \
    get_session_application_invoice, delete_session_application_invoice, set_session_dcv_permit_invoice, \
    get_session_dcv_permit_invoice, delete_session_dcv_permit_invoice
from mooringlicensing.components.proposals.models import Proposal
from mooringlicensing.components.proposals.utils import proposal_submit


logger = logging.getLogger('payment_checkout')


class DcvPermitFeeView(TemplateView):
    # template_name = 'disturbance/payment/success.html'

    def get_object(self):
        return get_object_or_404(DcvPermit, id=self.kwargs['dcv_permit_pk'])

    def post(self, request, *args, **kwargs):
        dcv_permit = self.get_object()
        dcv_permit_fee = DcvPermitFee.objects.create(dcv_permit=dcv_permit, created_by=request.user, payment_type=DcvPermitFee.PAYMENT_TYPE_TEMPORARY)

        try:
            with transaction.atomic():
                set_session_dcv_permit_invoice(request.session, dcv_permit_fee)

                lines, db_processes_after_success = create_fee_lines(dcv_permit)

                request.session['db_processes'] = db_processes_after_success
                checkout_response = checkout(
                    request,
                    dcv_permit,
                    lines,
                    return_url_ns='dcv_permit_fee_success',
                    return_preload_url_ns='dcv_permit_fee_success',
                    invoice_text='Application Fee',
                )

                logger.info('{} built payment line item {} for DcvPermit Fee and handing over to payment gateway'.format(request.user, dcv_permit.id))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating DcvPermit Fee: {}'.format(e))
            if dcv_permit_fee:
                dcv_permit_fee.delete()
            raise


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
                    proposal,
                    lines,
                    return_url_ns='fee_success',
                    return_preload_url_ns='fee_success',
                    invoice_text='DcvPermit Fee',
                )

                logger.info('{} built payment line item {} for Application Fee and handing over to payment gateway'.format('User {} with id {}'.format(proposal.submitter.get_full_name(),proposal.submitter.id), proposal.id))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating Application Fee: {}'.format(e))
            if application_fee:
                application_fee.delete()
            raise


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

            fee_constructor = FeeConstructor.objects.get(id=db_operations['fee_constructor_id'])

            # Update the application_fee object
            dcv_permit_fee.invoice_reference = invoice_ref
            dcv_permit_fee.fee_constructor = fee_constructor
            dcv_permit_fee.save()

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
                if inv.system != fee_constructor.application_type.oracle_code:
                    logger.error('{} tried paying an dcv_permit fee with an invoice from another system with reference number {}'.format('User {} with id {}'.format(dcv_permit.submitter.get_full_name(), dcv_permit.submitter.id) if dcv_permit.submitter else 'An anonymous user',inv.reference))
                    return redirect('external-dcv_permit-detail', args=(dcv_permit.id,))

                # if fee_inv:
                dcv_permit_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                dcv_permit_fee.expiry_time = None
                update_payments(invoice_ref)

                if dcv_permit and invoice.payment_status in ('paid', 'over_paid',):
                    self.adjust_db_operations(dcv_permit, db_operations)
                    # proposal_submit(proposal, request)
                else:
                    logger.error('Invoice payment status is {}'.format(invoice.payment_status))
                    raise

                dcv_permit_fee.save()
                request.session[self.LAST_DCV_PERMIT_FEE_ID] = dcv_permit_fee.id
                delete_session_dcv_permit_invoice(request.session)

                DcvPermitFeeSuccessView.send_invoice_mail(dcv_permit, invoice, request)
                # send_application_fee_invoice_apiary_email_notification(request, proposal, invoice, recipients=[recipient])
                #send_application_fee_confirmation_apiary_email_notification(request, application_fee, invoice, recipients=[recipient])
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

    @staticmethod
    def send_invoice_mail(dcv_permit, invoice, request):
        # Send invoice
        to_email_addresses = dcv_permit.submitter.email
        email_data = send_dcv_permit_fee_invoice(dcv_permit, invoice, [to_email_addresses, ])

        # Add comms log
        # TODO: Add comms log
        # email_data['approval'] = u'{}'.format(dcv_permit_fee.approval.id)
        # serializer = ApprovalLogEntrySerializer(data=email_data)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()

        # Check if the request.user can access the invoice
        can_access_invoice = False
        if not request.user.is_anonymous():
            # if request.user == dcv_permit_fee.submitter or dcv_permit_fee.approval.applicant in request.user.disturbance_organisations.all():
            if request.user == dcv_permit.submitter:
                can_access_invoice = True

        return can_access_invoice, to_email_addresses


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

            fee_constructor = FeeConstructor.objects.get(id=db_operations['fee_constructor_id'])

            # Update the application_fee object
            application_fee.invoice_reference = invoice_ref
            application_fee.fee_constructor = fee_constructor
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
                if inv.system not in ['0517']:
                    logger.error('{} tried paying an application fee with an invoice from another system with reference number {}'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user',inv.reference))
                    return redirect('external-proposal-detail', args=(proposal.id,))

                # if fee_inv:
                application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                application_fee.expiry_time = None
                update_payments(invoice_ref)

                if proposal and invoice.payment_status in ('paid', 'over_paid',):
                    self.adjust_db_operations(db_operations)
                    proposal_submit(proposal, request)
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

