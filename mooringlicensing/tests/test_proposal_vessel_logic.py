from mooringlicensing.settings import HTTP_HOST_FOR_TEST
from mooringlicensing.tests.test_setup import APITestSetup


class VesselTests(APITestSetup):
    def test_proposal_wla_vessel_logic(self):
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
        #proposal = Proposal.objects.get(id=proposal_id)
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
                        "percentage": "23", 
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

