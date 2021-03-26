import logging

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

from mooringlicensing.components.payments_ml.models import ApplicationFee
from mooringlicensing.components.payments_ml.utils import checkout, create_fee_lines, set_session_application_invoice, \
    get_session_application_invoice, delete_session_application_invoice
from mooringlicensing.components.proposals.models import Proposal


logger = logging.getLogger('payment_checkout')


class ApplicationFeeView(TemplateView):
    template_name = 'disturbance/payment/success.html'

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs['proposal_pk'])

    def post(self, request, *args, **kwargs):
        print('ApplicationFeeView.post()')

        proposal = self.get_object()
        application_fee = ApplicationFee.objects.create(proposal=proposal, created_by=request.user, payment_type=ApplicationFee.PAYMENT_TYPE_TEMPORARY)

        try:
            with transaction.atomic():
                set_session_application_invoice(request.session, application_fee)

                # TODO implement this function correctly
                lines, db_processes_after_success = create_fee_lines(proposal)

                request.session['db_processes'] = db_processes_after_success
                checkout_response = checkout(
                    request,
                    proposal,
                    lines,
                    return_url_ns='fee_success',
                    return_preload_url_ns='fee_success',
                    invoice_text='Application Fee',
                )

                logger.info('{} built payment line item {} for Application Fee and handing over to payment gateway'.format('User {} with id {}'.format(proposal.submitter.get_full_name(),proposal.submitter.id), proposal.id))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating Application Fee: {}'.format(e))
            if application_fee:
                application_fee.delete()
            raise


class ApplicationFeeSuccessView(TemplateView):
    template_name = 'mooringlicensing/payments_ml/success_fee.html'
    LAST_APPLICATION_FEE_ID = 'mooringlicensing_last_app_invoice'

    def get(self, request, *args, **kwargs):
        print('ApplicationFeeSuccessView.get()')

        try:
            # Retrieve db processes stored when calculating the fee, and delete the session
            db_operations = request.session['db_processes']
            del request.session['db_processes']

            application_fee = get_session_application_invoice(request.session)  # This raises an exception when accessed 2nd time?
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
                if inv.system not in ['0517']:
                    logger.error('{} tried paying an application fee with an invoice from another system with reference number {}'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user',inv.reference))
                    return redirect('external-proposal-detail', args=(proposal.id,))

                # if fee_inv:
                application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                application_fee.expiry_time = None
                update_payments(invoice_ref)

                if proposal and (invoice.payment_status == 'paid' or invoice.payment_status == 'over_paid'):
                    # if isinstance(proposal.fee_invoice_references, list):
                    #     proposal.fee_invoice_references.append(invoice_ref)
                    # else:
                    #     proposal.fee_invoice_references = [invoice_ref,]
                    # proposal.save()
                    self.adjust_db_operations(db_operations)
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
                    'fee_invoice': invoice,
                }
                return render(request, self.template_name, context)

        except Exception as e:
            print('in ApplicationFeeSuccessView.get() Exception')
            if (self.LAST_APPLICATION_FEE_ID in request.session) and ApplicationFee.objects.filter(id=request.session[self.LAST_APPLICATION_FEE_ID]).exists():
                application_fee = ApplicationFee.objects.get(id=request.session[self.LAST_APPLICATION_FEE_ID])
                proposal = application_fee.proposal

                recipient = proposal.applicant_email
                submitter = proposal.submitter

            else:
                return redirect('home')

        context = {
            'proposal': proposal,
            'submitter': submitter,
            'fee_invoice': application_fee,
        }
        return render(request, self.template_name, context)

    def adjust_db_operations(self, db_operations):
        return


        proposal_apiary = ProposalApiary.objects.get(id=db_operations['proposal_apiary_id'])

        proposal_apiary.post_payment_success()
        # non vacant site
        # for site_id in db_operations['apiary_site_ids']:
        #     apiary_site = ApiarySite.objects.get(id=site_id)
        #     proposal_apiary.set_status(apiary_site, ApiarySiteOnProposal.SITE_STATUS_PENDING)

        # vacant site
        # for site_id in db_operations['vacant_apiary_site_ids']:
        #     apiary_site = ApiarySite.objects.get(id=site_id,)
        #     apiary_site.is_vacant = False
        #     apiary_site.save()
        #     proposal_apiary.set_status(apiary_site, ApiarySiteOnProposal.SITE_STATUS_PENDING)

        # Perform database operations to remove and/or store site remainders
        # site remainders used
        for item in db_operations['site_remainder_used']:
            site_remainder = ApiarySiteFeeRemainder.objects.get(id=item['id'])
            site_remainder.date_used = datetime.strptime(item['date_used'], '%Y-%m-%d')
            site_remainder.save()

        # site remainders added
        for item in db_operations['site_remainder_to_be_added']:
            apiary_site_fee_type = ApiarySiteFeeType.objects.get(name=item['apiary_site_fee_type_name'])
            site_category = SiteCategory.objects.get(id=item['site_category_id'])
            # date_expiry = datetime.strptime(item['date_expiry'], '%Y-%m-%d')
            applicant = Organisation.objects.get(id=item['applicant_id']) if item['applicant_id'] else None
            proxy_applicant = EmailUser.objects.get(id=item['proxy_applicant_id']) if item[
                'proxy_applicant_id'] else None

            site_remainder = ApiarySiteFeeRemainder.objects.create(
                site_category=site_category,
                apiary_site_fee_type=apiary_site_fee_type,
                applicant=applicant,
                proxy_applicant=proxy_applicant,
            )


class InvoicePDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, reference=self.kwargs['reference'])
        # url_var = apiary_url(request)

        try:
            # Assume the invoice has been issued for the application(proposal)
            # proposal = Proposal.objects.get(fee_invoice_reference=invoice.reference)
            # proposal = Proposal.objects.get(invoice_references__contains=[invoice.reference])
            application_fee = ApplicationFee.objects.get(invoice_reference=invoice.reference)
            proposal = application_fee.proposal

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
        except Proposal.DoesNotExist:
            # The invoice might be issued for the annual site fee
            # annual_rental_fee = AnnualRentalFee.objects.get(invoice_reference=invoice.reference)
            # approval = annual_rental_fee.approval
            response = HttpResponse(content_type='application/pdf')
            # response.write(create_invoice_pdf_bytes('invoice.pdf', invoice, url_var, None))
            response.write(create_invoice_pdf_bytes('invoice.pdf', invoice,))
            return response
        except:
            raise

    def get_object(self):
        return get_object_or_404(Invoice, reference=self.kwargs['reference'])

    # def check_owner(self, organisation):
    #     return is_in_organisation_contacts(self.request, organisation) or is_internal(self.request) or self.request.user.is_superuser

