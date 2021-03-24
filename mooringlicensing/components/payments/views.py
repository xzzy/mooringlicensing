import logging

from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from mooringlicensing.components.payments.utils import checkout, create_fee_lines
from mooringlicensing.components.proposals.models import Proposal


logger = logging.getLogger('payment_checkout')


class ApplicationFeeView(TemplateView):
    template_name = 'disturbance/payment/success.html'

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs['proposal_pk'])

    def post(self, request, *args, **kwargs):

        proposal = self.get_object()
        # application_fee = ApplicationFee.objects.create(proposal=proposal, created_by=request.user, payment_type=ApplicationFee.PAYMENT_TYPE_TEMPORARY)

        try:
            with transaction.atomic():
                # if proposal.application_type.name == ApplicationType.SITE_TRANSFER:
                #     set_session_site_transfer_application_invoice(request.session, application_fee)
                # else:
                #     set_session_application_invoice(request.session, application_fee)
                # lines, db_processes_after_success = create_fee_lines(proposal)
                lines = create_fee_lines(proposal)

                checkout_response = checkout(
                    request,
                    proposal,
                    lines,
                    return_url_ns='fee_success',
                    return_preload_url_ns='fee_success',
                    invoice_text='Application Fee',
                )
                #import ipdb; ipdb.set_trace()
                # Store site remainders data in this session, which is retrieved once payment success (ref: ApplicationFeeSuccessView below)
                # then based on that, site remainders data is updated

                # if proposal.application_type.name == ApplicationType.SITE_TRANSFER:
                #     checkout_response = checkout(
                #         request,
                #         proposal,
                #         lines,
                #         return_url_ns='site_transfer_fee_success',
                #         return_preload_url_ns='site_transfer_fee_success',
                #         invoice_text='Site Transfer Application Fee'
                #     )
                # else:
                #     request.session['db_processes'] = db_processes_after_success
                #     checkout_response = checkout(
                #         request,
                #         proposal,
                #         lines,
                #         return_url_ns='fee_success',
                #         return_preload_url_ns='fee_success',
                #         invoice_text='Application Fee'
                #     )

                logger.info('{} built payment line item {} for Application Fee and handing over to payment gateway'.format('User {} with id {}'.format(proposal.submitter.get_full_name(),proposal.submitter.id), proposal.id))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating Application Fee: {}'.format(e))
            # if application_fee:
            #     application_fee.delete()
            raise


class ApplicationFeeSuccessView(TemplateView):
    template_name = 'mooringlicensing/payments/success_fee.html'

    def get(self, request, *args, **kwargs):
        proposal = None
        submitter = None
        invoice = None
        try:
            ###################
            raise
            ###################

            # Retrieve db processes stored when calculating the fee, and delete the session
            db_operations = request.session['db_processes']
            del request.session['db_processes']

            application_fee = get_session_application_invoice(request.session)
            proposal = application_fee.proposal
            try:
                if proposal.applicant:
                    recipient = proposal.applicant.email
                    #submitter = proposal.applicant
                elif proposal.proxy_applicant:
                    recipient = proposal.proxy_applicant.email
                    #submitter = proposal.proxy_applicant
                else:
                    recipient = proposal.submitter.email
                    #submitter = proposal.submitter
            except:
                recipient = proposal.submitter.email
            submitter = proposal.submitter

            if self.request.user.is_authenticated():
                basket = Basket.objects.filter(status='Submitted', owner=request.user).order_by('-id')[:1]
            else:
                basket = Basket.objects.filter(status='Submitted', owner=booking.proposal.submitter).order_by('-id')[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)
            invoice_ref = invoice.reference
            fee_inv, created = ApplicationFeeInvoice.objects.get_or_create(application_fee=application_fee, invoice_reference=invoice_ref)

            if application_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=inv.order_number)
                    #order.user = submitter
                    order.user = request.user
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error('{} tried paying an application fee with an incorrect invoice'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user'))
                    return redirect('external-proposal-detail', args=(proposal.id,))
                if inv.system not in ['0517']:
                    logger.error('{} tried paying an application fee with an invoice from another system with reference number {}'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user',inv.reference))
                    return redirect('external-proposal-detail', args=(proposal.id,))

                if fee_inv:
                    #application_fee.payment_type = 1  # internet booking
                    application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                    application_fee.expiry_time = None
                    update_payments(invoice_ref)

                    if proposal and (invoice.payment_status == 'paid' or invoice.payment_status == 'over_paid'):
                        # proposal.fee_invoice_reference = invoice_ref
                        if isinstance(proposal.fee_invoice_references, list):
                            proposal.fee_invoice_references.append(invoice_ref)
                        else:
                            proposal.fee_invoice_references = [invoice_ref,]
                        proposal.save()
                        proposal_submit_apiary(proposal, request)
                        self.adjust_db_operations(db_operations)
                    else:
                        logger.error('Invoice payment status is {}'.format(invoice.payment_status))
                        raise

                    application_fee.save()
                    request.session['das_last_app_invoice'] = application_fee.id
                    delete_session_application_invoice(request.session)

                    send_application_fee_invoice_apiary_email_notification(request, proposal, invoice, recipients=[recipient])
                    #send_application_fee_confirmation_apiary_email_notification(request, application_fee, invoice, recipients=[recipient])
                    context = {
                        'proposal': proposal,
                        'submitter': submitter,
                        'fee_invoice': invoice
                    }
                    return render(request, self.template_name, context)

        except Exception as e:
            ###################
            context = {
                'proposal': proposal,
                'submitter': 'test submitter',
                'fee_invoice': None
            }
            return render(request, self.template_name, context)
            ###################

            if ('das_last_app_invoice' in request.session) and ApplicationFee.objects.filter(id=request.session['das_last_app_invoice']).exists():
                application_fee = ApplicationFee.objects.get(id=request.session['das_last_app_invoice'])
                proposal = application_fee.proposal

                try:
                    if proposal.applicant:
                        recipient = proposal.applicant.email
                        #submitter = proposal.applicant
                    elif proposal.proxy_applicant:
                        recipient = proposal.proxy_applicant.email
                        #submitter = proposal.proxy_applicant
                    else:
                        recipient = proposal.submitter.email
                        #submitter = proposal.submitter
                except:
                    recipient = proposal.submitter.email
                submitter = proposal.submitter

                if ApplicationFeeInvoice.objects.filter(application_fee=application_fee).count() > 0:
                    afi = ApplicationFeeInvoice.objects.filter(application_fee=application_fee)
                    fee_invoice = afi[0]
            else:
                return redirect('home')

        context = {
            'proposal': proposal,
            'submitter': submitter,
            'fee_invoice': fee_invoice
        }
        return render(request, self.template_name, context)

    def adjust_db_operations(self, db_operations):
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

