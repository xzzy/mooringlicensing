from mooringlicensing.settings import HTTP_HOST_FOR_TEST
from mooringlicensing.tests.test_setup import APITestSetup
from mooringlicensing.components.proposals.models import MooringBay, Proposal, Vessel
from mooringlicensing.components.proposals.utils import proposal_submit
from datetime import datetime
import pytz
from ledger.settings_base import TIME_ZONE
#from mooringlicensing.tests.test_manage_vessels import ManageVesselTests


class VesselTests(APITestSetup):
    #def test_proposal_wla_vessel_logic(self):
        #self.wla_vessel_logic()

    def test_create_bare_vessel_add_to_proposal(self):
        create_vessel_data = {
                'vessel': {
                    'new_vessel': True, 
                    'rego_no': '20210503_1', 
                    'vessel_details': {
                        'read_only': False, 
                        'vessel_name': '20210503_1', 
                        'berth_mooring': 'home', 
                        'vessel_length': '23', 
                        'vessel_overall_length': '34',
                        'vessel_weight': '45', 
                        'vessel_draft': '56', 
                        'vessel_type': 'tender'
                        }, 
                    'vessel_ownership': {
                        'registered_owner': 'current_user', 
                        'individual_owner': True, 
                        'percentage': '35'
                        }
                    }
                }

        self.client.login(email=self.customer1, password='pass')
        self.client.enforce_csrf_checks=True
        create_response = self.client.post(
            '/api/vessel/',
            #self.create_proposal_data,
            create_vessel_data,
            format='json',
            HTTP_HOST=HTTP_HOST_FOR_TEST,
        )

        #vessel_details_id_1 = create_response.data.get('vessel_details').get('id')
        vessel_id_1 = create_response.data.get('id')
        vessel = Vessel.objects.get(id=vessel_id_1)
        vessel_details_id_1 = vessel.latest_vessel_details.id

        #import ipdb; ipdb.set_trace()
        #manage_vessel_test_cases = ManageVesselTests()
        #vessel_id_1, vessel_details_id_1  = manage_vessel_test_cases.test_manage_vessels()

        ## vessel is now in 'draft' status
        #vessel_details_id_1 = proposal.vessel_details.id
        #vessel_ownership_id_1 = proposal.vessel_ownership.id
        #vessel_id_1 = proposal.vessel_details.vessel_id

        ## Proposal 2 - add vessel from Proposal
        create_response_2 = self.client.post(
            '/api/waitinglistapplication/',
            #self.create_proposal_data,
            format='json',
            HTTP_HOST=HTTP_HOST_FOR_TEST,
        )

        self.assertEqual(create_response_2.status_code, 200)
        self.assertTrue(create_response_2.data.get('id') > 0)

        proposal_2_id = create_response_2.data.get('id')
        # get proposal
        url2 = 'http://localhost:8071/api/proposal/{}.json'.format(proposal_2_id)
        get_response_2 = self.client.get(url2, HTTP_HOST=HTTP_HOST_FOR_TEST,)

        self.assertEqual(get_response_2.status_code, 200)
        # save Proposal2
        draft_proposal_data = {
                "proposal": {}, 
                "vessel": {
                    "vessel_details": {
                        "id": vessel_details_id_1
                        }, 
                    "vessel_ownership": {
                        #"id": vessel_ownership_id_1
                        }, 
                    "id": vessel_id_1,
                    "read_only": True,
                    }
                }

        draft_response = self.client.post(
                '/api/proposal/{}/draft/'.format(proposal_2_id),
                draft_proposal_data, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(draft_response.status_code, 302)
        

        ## add DoT rego papers
        rego_papers_response = self.client.post(
                '/api/proposal/{}/process_vessel_registration_document/'.format(proposal_2_id),
                self.rego_papers_data, 
                #format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(rego_papers_response.status_code, 200)

        # submit Proposal2
        # submit api endpoint
        submit_proposal_2_data = {
                "proposal": {
                    "preferred_bay_id": MooringBay.objects.last().id,
                    "silent_elector": False,
                    }, 
                "vessel": {
                    "vessel_details": {
                        "id": vessel_details_id_1
                        }, 
                    "vessel_ownership": {
                        #"id": vessel_ownership_id_1
                        "org_name": "Company1", 
                        "percentage": "65", # increase to 66 to cause serializer validation error 
                        "individual_owner": False
                        }, 
                    "id": vessel_id_1,
                    "read_only": True,
                    }
                }
        submit_2_response = self.client.post(
                '/api/proposal/{}/submit/'.format(proposal_2_id),
                submit_proposal_2_data, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(submit_2_response.status_code, 200)

        ### proposal_submit(instance, request) - need a request obj, so we just make changes manually here
        #proposal_2 = Proposal.objects.get(id=proposal_2_id)
        #proposal_2.lodgement_date = datetime.now(pytz.timezone(TIME_ZONE))
        #proposal_2.processing_status = 'with_assessor'
        #proposal_2.customer_status = 'with_assessor'
        #proposal_2.save()
        ## proposal and proposal2 should now share the same vessel_details
        #self.assertEqual(proposal.vessel_details, proposal_2.vessel_details)
        #self.assertEqual(proposal.vessel_ownership.vessel, proposal_2.vessel_ownership.vessel)
        #self.assertNotEqual(proposal.vessel_ownership, proposal_2.vessel_ownership)


    def test_proposal_wla_vessel_logic(self):
    #def wla_vessel_logic(self):
        print("test_proposal_wla_vessel_logic")
        self.client.login(email=self.customer, password='pass')
        self.client.enforce_csrf_checks=True
        create_response = self.client.post(
            '/api/waitinglistapplication/',
            #self.create_proposal_data,
            format='json',
            HTTP_HOST=HTTP_HOST_FOR_TEST,
        )

        self.assertEqual(create_response.status_code, 200)
        self.assertTrue(create_response.data.get('id') > 0)

        proposal_id = create_response.data.get('id')
        # get proposal
        url = 'http://localhost:8071/api/proposal/{}.json'.format(proposal_id)
        get_response = self.client.get(url, HTTP_HOST=HTTP_HOST_FOR_TEST,)

        self.assertEqual(get_response.status_code, 200)
        #######################
        draft_proposal_data = {
                "proposal": {}, 
                "vessel": {
                    "vessel_details": {
                        "vessel_type": "cabin_cruiser", 
                        "vessel_name": "gfhj", 
                        "vessel_overall_length": "45", 
                        "vessel_length": "34", 
                        "vessel_draft": "67", 
                        "vessel_beam": "0.00", 
                        "vessel_weight": "56", 
                        "berth_mooring": "fghx"
                        }, 
                    "vessel_ownership": {
                        "org_name": None, 
                        "percentage": "26", 
                        "individual_owner": None
                        }, 
                    "rego_no": "20210407_1", 
                    "vessel_id": None
                    }
                }

        draft_response = self.client.post(
                '/api/proposal/{}/draft/'.format(proposal_id),
                draft_proposal_data, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(draft_response.status_code, 302)

        ## add DoT rego papers
        rego_papers_response = self.client.post(
                '/api/proposal/{}/process_vessel_registration_document/'.format(proposal_id),
                self.rego_papers_data, 
                #format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(rego_papers_response.status_code, 200)

        ## add Silent Elector papers
        electoral_roll_doc_response = self.client.post(
                '/api/proposal/{}/process_electoral_roll_document/'.format(proposal_id),
                self.electoral_roll_doc_data, 
                #format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(electoral_roll_doc_response.status_code, 200)

        ## submit api endpoint
        #submit_proposal_data = {
        #        "proposal": {
        #            "preferred_bay_id": MooringBay.objects.first().id,
        #            }
        #        }
        submit_proposal_data = {
                "proposal": {
                    "silent_elector": True,
                    "preferred_bay_id": MooringBay.objects.first().id,
                    }, 
                "vessel": {
                    "vessel_details": {
                        "vessel_type": "cabin_cruiser", 
                        "vessel_name": "gfhj", 
                        "vessel_overall_length": "45", 
                        "vessel_length": "34", 
                        "vessel_draft": "67", 
                        "vessel_beam": "0.00", 
                        "vessel_weight": "56", 
                        "berth_mooring": "fghx"
                        }, 
                    "vessel_ownership": {
                        "org_name": None, 
                        "percentage": "26", 
                        "individual_owner": True
                        }, 
                    "rego_no": "20210407_1", 
                    "vessel_id": None
                    }
                }

        submit_response = self.client.post(
                '/api/proposal/{}/submit/'.format(proposal_id),
                submit_proposal_data, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(submit_response.status_code, 200)

        ## proposal_submit(instance, request) - need a request obj, so we just make changes manually here
        proposal = Proposal.objects.get(id=proposal_id)
        proposal.lodgement_date = datetime.now(pytz.timezone(TIME_ZONE))
        proposal.processing_status = 'with_assessor'
        proposal.customer_status = 'with_assessor'
        proposal.save()

        ## vessel is now in 'draft' status
        vessel_details_id_1 = proposal.vessel_details.id
        vessel_ownership_id_1 = proposal.vessel_ownership.id
        vessel_id_1 = proposal.vessel_details.vessel_id

        ## Proposal 2 - add vessel from Proposal
        create_response_2 = self.client.post(
            '/api/waitinglistapplication/',
            #self.create_proposal_data,
            format='json',
            HTTP_HOST=HTTP_HOST_FOR_TEST,
        )

        self.assertEqual(create_response_2.status_code, 200)
        self.assertTrue(create_response_2.data.get('id') > 0)

        proposal_2_id = create_response_2.data.get('id')
        # get proposal
        url2 = 'http://localhost:8071/api/proposal/{}.json'.format(proposal_2_id)
        get_response_2 = self.client.get(url2, HTTP_HOST=HTTP_HOST_FOR_TEST,)

        self.assertEqual(get_response_2.status_code, 200)
        # save Proposal2
        draft_proposal_data = {
                "proposal": {}, 
                "vessel": {
                    "vessel_details": {
                        "id": vessel_details_id_1
                        }, 
                    "vessel_ownership": {
                        #"id": vessel_ownership_id_1
                        }, 
                    "id": vessel_id_1,
                    "read_only": True,
                    }
                }

        draft_response = self.client.post(
                '/api/proposal/{}/draft/'.format(proposal_2_id),
                draft_proposal_data, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(draft_response.status_code, 302)
        

        ## add DoT rego papers
        rego_papers_response = self.client.post(
                '/api/proposal/{}/process_vessel_registration_document/'.format(proposal_2_id),
                self.rego_papers_data, 
                #format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(rego_papers_response.status_code, 200)

        # submit Proposal2
        # submit api endpoint
        submit_proposal_2_data = {
                "proposal": {
                    "preferred_bay_id": MooringBay.objects.last().id,
                    "silent_elector": False,
                    }, 
                "vessel": {
                    "vessel_details": {
                        "id": vessel_details_id_1
                        }, 
                    "vessel_ownership": {
                        #"id": vessel_ownership_id_1
                        "org_name": "Company1", 
                        "percentage": "26", 
                        "individual_owner": False
                        }, 
                    "id": vessel_id_1,
                    "read_only": True,
                    }
                }
        submit_2_response = self.client.post(
                '/api/proposal/{}/submit/'.format(proposal_2_id),
                submit_proposal_2_data, 
                format='json',
                HTTP_HOST=HTTP_HOST_FOR_TEST,
        )
        self.assertEqual(submit_2_response.status_code, 200)

        ## proposal_submit(instance, request) - need a request obj, so we just make changes manually here
        proposal_2 = Proposal.objects.get(id=proposal_2_id)
        proposal_2.lodgement_date = datetime.now(pytz.timezone(TIME_ZONE))
        proposal_2.processing_status = 'with_assessor'
        proposal_2.customer_status = 'with_assessor'
        proposal_2.save()
        # proposal and proposal2 should now share the same vessel_details
        self.assertEqual(proposal.vessel_details, proposal_2.vessel_details)
        self.assertEqual(proposal.vessel_ownership.vessel, proposal_2.vessel_ownership.vessel)
        self.assertNotEqual(proposal.vessel_ownership, proposal_2.vessel_ownership)

