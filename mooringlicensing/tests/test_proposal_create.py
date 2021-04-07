from mooringlicensing.settings import HTTP_HOST_FOR_TEST
from mooringlicensing.tests.test_setup import APITestSetup


class ProposalTests(APITestSetup):
    def test_create_proposal_wla(self):
        print("test_create_proposal_wla")
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

    def test_create_proposal_aaa(self):
        print("test_create_proposal_aaa")
        self.client.login(email=self.customer, password='pass')
        self.client.enforce_csrf_checks=True
        create_response = self.client.post(
            '/api/annualadmissionapplication/',
            #self.create_proposal_data,
            format='json',
            HTTP_HOST=HTTP_HOST_FOR_TEST,
        )

        self.assertEqual(create_response.status_code, 200)
        self.assertTrue(create_response.data.get('id') > 0)

