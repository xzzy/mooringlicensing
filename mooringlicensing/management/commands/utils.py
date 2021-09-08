def ml_meet_vessel_requirement(mooring_licence, boundary_date):
    # Return True when mooring_licence has at least one vessel whoose size is more than 6.4m and not sold or sold after the boundary_date
    for proposal in mooring_licence.proposal_set.all():
        if proposal.vessel_details and proposal.vessel_details.vessel and proposal.vessel_details.vessel.latest_vessel_details and proposal.vessel_details.vessel.latest_vessel_details.vessel_applicable_length >= 6.4:
            # Vessel meets the length requirements
            if proposal.vessel_ownership.end_date is None or proposal.vessel_ownership.end_date > boundary_date:
                # Vessel not sold or sold just recently
                return True
    return False