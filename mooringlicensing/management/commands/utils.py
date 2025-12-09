from django.db.models import F

from mooringlicensing.components.main.models import GlobalSettings

from mooringlicensing.components.approvals.models import (
    Approval, Sticker
)

from mooringlicensing.components.proposals.models import (
    Proposal, VesselOwnership
)

import datetime

def get_unaccounted_sold_vessel_ownerships(proposals):
    """Get vessel ownerships for vessels that have been sold but have no end date, excluding records created after the latest sold vessel ownership record"""
    proposals_with_vo = proposals.exclude(vessel_ownership=None)
    proposal_vo_ids = list(proposals_with_vo.values_list("vessel_ownership_id", flat=True))
    vessel_ownerships = VesselOwnership.objects.filter(id__in=proposal_vo_ids)

    sold_vessel_ownerships = vessel_ownerships.exclude(end_date=None)
    unsold_vessel_ownerships = vessel_ownerships.filter(end_date=None)
    rego_nos = []
    for svo in sold_vessel_ownerships:
        if svo.vessel:
            if unsold_vessel_ownerships.filter(created__lt=svo.created,owner=svo.owner,vessel__rego_no=svo.vessel.rego_no).exists():
                rego_nos.append(svo.vessel.rego_no)
    return ("Vessels that have been marked as sold have unaccounted for vessel ownership records and possibly related records that have not been marked as sold:", rego_nos)

#NOTE: with changes to sales handling this particular report is no longer required but may be useful for debugging
def check_duplicate_vessel_ownerships_among_proposals(proposals):
    """reporting function for checking for multiple vessel ownerships among proposals (pertaining to different current approvals) that have not ended (should only be one)"""
    proposals_with_vo = proposals.exclude(vessel_ownership=None).filter(approval__current_proposal_id=F('id')).filter(approval__status__in=Approval.APPROVED_STATUSES)
    proposal_vo_ids = list(proposals_with_vo.values_list("vessel_ownership_id", flat=True))
    vessel_ownerships = VesselOwnership.objects.filter(id__in=proposal_vo_ids, end_date=None)

    accounted_for = []
    multiples = []
    #records here are in-date and assigned to the provided proposals - so if multiple have the same rego no something is wrong
    for vo in vessel_ownerships:
        if vo.vessel:
            if vo.vessel.rego_no in accounted_for and not vo in multiples:
                multiples.append(vo.vessel.rego_no)
            else:
                accounted_for.append(vo.vessel.rego_no)

    multiples_with_proposals = []
    for rego_no in multiples:
        multiples_with_proposals.append(f'{rego_no} ({",".join(list(proposals_with_vo.filter(vessel_ownership__vessel__rego_no=rego_no).values_list("lodgement_number",flat=True)))})')

    return ("Vessels with multiple ongoing vessel ownerships on multiple proposal records that pertain to different current approvals) (only should be one at a time):", multiples_with_proposals)

def check_proposal_stuck_at_printing(proposals):
    """reporting function for checking proposals stuck in printing sticker despite no sticker records awaiting printing or export"""
    printing = proposals.filter(processing_status=Proposal.PROCESSING_STATUS_PRINTING_STICKER)
    stickers = Sticker.objects.filter(proposal_initiated_id__in=list(printing.values_list('id',flat=True)))
    non_printing_stickers = stickers.exclude(status__in=[Sticker.STICKER_STATUS_AWAITING_PRINTING, Sticker.STICKER_STATUS_READY, Sticker.STICKER_STATUS_NOT_READY_YET])
    non_printing_proposal_ids = list(non_printing_stickers.values_list('id', flat=True))

    non_printing_stuck = list(printing.filter(id__in=non_printing_proposal_ids).values_list('lodgement_number',flat=True))

    return ("Proposals with a Printing Sticker status but with no Sticker records awaiting printing or awaiting export.", non_printing_stuck)

def check_invalid_expired_approval(approvals):
    """reporting function to get all expired approvals that have a later expiry date"""
    current_time = datetime.datetime.now()
    expired_approvals_bad_dates = approvals.filter(status=Approval.APPROVAL_STATUS_CURRENT, expiry_date__lt=current_time)

    if expired_approvals_bad_dates.exists():
        numbers = list(expired_approvals_bad_dates.values_list("lodgement_number",flat=True))
        return ("Approvals with an Expired status but still in date:", numbers)

def ml_meet_vessel_requirement(mooring_licence, boundary_date):
    min_length_setting = GlobalSettings.objects.get(key=GlobalSettings.KEY_MINUMUM_MOORING_VESSEL_LENGTH)
    min_length = float(min_length_setting.value)

    # Return True when mooring_licence has at least one vessel whoose size is more than 6.4m and not sold or sold after the boundary_date
    for proposal in mooring_licence.proposal_set.all():
        if proposal.vessel_details and proposal.vessel_details.vessel and proposal.vessel_details.vessel.latest_vessel_details and proposal.vessel_details.vessel.latest_vessel_details.vessel_applicable_length >= min_length:
            # Vessel meets the length requirements
            if proposal.vessel_ownership.end_date is None or proposal.vessel_ownership.end_date > boundary_date:
                # At least one vessel has not been sold or sold recently
                return True

    # All the vessels have been sold more than X months ago
    return False

def construct_email_message(cmd_name, errors, updates):
    cmd_str = '<div>{} completed.</div>'.format(cmd_name)

    if len(errors) > 0:
        err_str = '<div><strong style="color: red;">Errors: {}</strong></div>'.format(len(errors))
        err_str += '<ul>'
        for error in errors:
            err_str += '<li>{}</li>'.format(error)
        err_str += '</ul>'
    else:
        err_str = '<div><strong style="color: green;">Errors: 0</strong></div>'

    updates_str = '<div>IDs updated: {}</div>'.format(updates)

    msg = '<div style="margin: 0 0 1em 0;">' + cmd_str + '<div style="margin:0 0 0 1em;">' + err_str + updates_str + '</div></div>'
    return msg
