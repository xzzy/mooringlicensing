<template lang="html">
    <div class="row">
        <div class="col-sm-12">
            <div class="col-md-12">
                        <div class="row">
                            <div class="panel panel-default">
                                <div class="panel-heading">
                                    <h3 class="panel-title">{{ customerLabel }}
                                        <a class="panelClicker" :href="'#'+detailsBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="detailsBody">
                                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                                        </a>
                                    </h3> 
                                </div>
                                <!--div v-if="applicantType == 'ORG'" class="panel-body panel-collapse collapse in" :id="detailsBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Name</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="proposal.org_applicant.name" style="width: 100%">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Trading Name</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="proposal.org_applicant.trading_name" style="width: 100%">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >ABN/ACN</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantABN" placeholder="" v-model="proposal.org_applicant.abn" style="width: 100%">
                                            </div>
                                          </div>

                                      </form>
                                </div-->
                                <div v-if="applicantType == 'SUB'" class="panel-body panel-collapse collapse in" :id="detailsBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Given Name(s)</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="email_user.first_name">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Surname</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="applicantName" placeholder="" v-model="email_user.last_name">
                                            </div>
                                          </div>
                                      </form>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-12">
                        <div class="row">
                            <div class="panel panel-default">
                                <div class="panel-heading">
                                    <h3 class="panel-title">Address Details
                                        <a class="panelClicker" :href="'#'+addressBody" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="addressBody">
                                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                        </a>
                                    </h3> 
                                </div>
                                <!--div v-if="applicantType == 'ORG' && proposal.org_applicant.address" class="panel-body panel-collapse collapse" :id="addressBody">
                                      <form class="form-horizontal">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Street</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="street" placeholder="" v-model="proposal.org_applicant.address.line1">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                                            <div class="col-sm-6">
                                                <input disabled type="text" class="form-control" name="surburb" placeholder="" v-model="proposal.org_applicant.address.locality">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">State</label>
                                            <div class="col-sm-2">
                                                <input disabled type="text" class="form-control" name="country" placeholder="" v-model="proposal.org_applicant.address.state">
                                            </div>
                                            <label for="" class="col-sm-2 control-label">Postcode</label>
                                            <div class="col-sm-2">
                                                <input disabled type="text" class="form-control" name="postcode" placeholder="" v-model="proposal.org_applicant.address.postcode">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Country</label>
                                            <div class="col-sm-4">
                                                <input disabled type="text" class="form-control" name="country" v-model="proposal.org_applicant.address.country"/>
                                            </div>
                                          </div>
                                       </form>
                                </div-->
                                <div v-if="applicantType == 'SUB' && email_user.residential_address" class="panel-body panel-collapse collapse" :id="addressBody">
                                  <form class="form-horizontal" action="index.html" method="post">
                                    <alert v-if="showAddressError" type="danger" style="color:red"><div v-for="item in errorListAddress"><strong>{{item}}</strong></div></alert>
                                  <div class="address-box">
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Residential Address</label>
                                        <div class="col-sm-6">
                                            <input :readonly="readonly" type="text" class="form-control" id="line1" name="Street" placeholder="" v-model="email_user.residential_address.line1">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                                        <div class="col-sm-6">
                                            <input :readonly="readonly" type="text" class="form-control" id="locality" name="Town/Suburb" placeholder="" v-model="email_user.residential_address.locality">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">State</label>
                                        <div class="col-sm-3">
                                            <input :readonly="readonly" type="text" class="form-control" id="state" name="State" placeholder="" v-model="email_user.residential_address.state">
                                        </div>
                                        <label for="" class="col-sm-1 control-label">Postcode</label>
                                        <div class="col-sm-2">
                                            <input :readonly="readonly" type="text" class="form-control" id="postcode" name="Postcode" placeholder="" v-model="email_user.residential_address.postcode">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Country</label>
                                        <div class="col-sm-4">
                                            <select :disabled="readonly" class="form-control" id="country" name="Country" v-model="email_user.residential_address.country">
                                                <option v-for="c in countries" :value="c.alpha2Code">{{ c.name }}</option>
                                            </select>
                                        </div>
                                      </div>
                                  </div>
                                      <!-- -->
                                  <div class="form-group"/>
                                  <div class="address-box">
                                      <div class="form-group">
                                        <div class="col-sm-3">
                                        </div>
                                        <div class="col-sm-6">
                                          <input :readonly="readonly" type="checkbox" id="postal_same_as_residential" v-model="email_user.postal_same_as_residential"/>
                                          <label for="postal_same_as_residential" class="control-label">Same as residential address</label>
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Postal Address</label>
                                        <div class="col-sm-6">
                                            <input :readonly="postalAddressReadonly" type="text" class="form-control" id="postal_line1" name="Street" placeholder="" v-model="email_user.postal_address.line1">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                                        <div class="col-sm-6">
                                            <input :readonly="postalAddressReadonly" type="text" class="form-control" id="postal_locality" name="Town/Suburb" placeholder="" v-model="email_user.postal_address.locality">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">State</label>
                                        <div class="col-sm-3">
                                            <input :readonly="postalAddressReadonly" type="text" class="form-control" id="postal_state" name="State" placeholder="" v-model="email_user.postal_address.state">
                                        </div>
                                        <label for="" class="col-sm-1 control-label">Postcode</label>
                                        <div class="col-sm-2">
                                            <input :readonly="postalAddressReadonly" type="text" class="form-control" id="postal_postcode" name="Postcode" placeholder="" v-model="email_user.postal_address.postcode">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Country</label>
                                        <div class="col-sm-4">
                                            <select :disabled="postalAddressReadonly" class="form-control" id="postal_country" name="Country" v-model="email_user.postal_address.country">
                                                <option v-for="c in countries" :value="c.alpha2Code">{{ c.name }}</option>
                                            </select>
                                        </div>
                                      </div>
                                  </div>

                                      <div class="form-group">
                                        <div v-if="!readonly" class="col-sm-12">
                                            <button v-if="!updatingAddress" class="pull-right btn btn-primary" @click.prevent="updateAddress()">Update</button>
                                            <button v-else disabled class="pull-right btn btn-primary"><i class="fa fa-spin fa-spinner"></i>&nbsp;Updating</button>
                                        </div>
                                      </div>
                                   </form>

                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-12">
                        <div class="row">
                            <div class="panel panel-default">
                                <div class="panel-heading">
                                    <h3 class="panel-title">Contact Details
                                        <a class="panelClicker" :href="'#'+contactsBody" data-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="contactsBody">
                                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                                        </a>
                                    </h3>
                                </div>
                                <!--div v-if="applicantType == 'ORG'" class="panel-body panel-collapse collapse" :id="contactsBody">
                                    <table ref="contacts_datatable" :id="contacts_table_id" class="hover table table-striped table-bordered dt-responsive" cellspacing="0" width="100%">
                                    </table>
                                </div-->
                                <div v-if="applicantType == 'SUB'" class="panel-body panel-collapse collapse" :id="contactsBody">
                                  <form class="form-horizontal">
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Phone (work)</label>
                                        <div class="col-sm-6">
                                            <input disabled type="text" class="form-control" name="applicantPhoneNumber" placeholder="" v-model="email_user.phone_number">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Mobile</label>
                                        <div class="col-sm-6">
                                            <input disabled type="text" class="form-control" name="applicantMobileNumber" placeholder="" v-model="email_user.mobile_number">
                                        </div>
                                      </div>
                                      <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Email</label>
                                        <div class="col-sm-6">
                                            <input disabled type="text" class="form-control" name="applicantEmail" placeholder="" v-model="email_user.email">
                                        </div>
                                      </div>
                                  </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
        <!-- <Assessment :proposal="proposal" :assessment="proposal.assessor_assessment" :hasAssessorMode="hasAssessorMode" :is_internal="is_internal" :is_referral="is_referral"></Assessment> -->
    </div>
</template>

<script>
//import Assessment from './assessment.vue'
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks'
    export default {
        name: 'Applicant',
        //props:["type","name","id", "comment_value","value","isRequired","help_text","help_text_assessor","assessorMode","label","readonly","assessor_readonly", "help_text_url", "help_text_assessor_url"],
        props:{
            //proposal:{
            //    type: Object,
            //    required: true,
            //},
            email_user: {
                type: Object,
                required: true,
            },
            applicantType: {
                type: String,
                required: true,
            },
            customerType: {
                type: String,
                required: false,
            },
        },
        data:function () {
            let vm=this;
            return{
                readonly: true,
                values:null,
                countries: [],
                showAddressError: false,
                detailsBody: 'detailsBody'+vm._uid,
                addressBody: 'addressBody'+vm._uid,
                contactsBody: 'contactsBody'+vm._uid,
                panelClickersInitialised: false,
                contacts_table_id: vm._uid+'contacts-table',
                contacts_table_initialised: false,
                contacts_options:{
                    language: {
                        processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                    },
                    responsive: true,
                    ajax: {
                        "url": vm.contactsURL,
                        "dataSrc": ''
                    },
                    columns: [
                        {
                            title: 'Name',
                            mRender:function (data,type,full) {
                                return full.first_name + " " + full.last_name;
                            }
                        },
                        {
                            title: 'Phone',
                            data:'phone_number'
                        },
                        {
                            title: 'Mobile',
                            data:'mobile_number'
                        },
                        {
                            title: 'Fax',
                            data:'fax_number'
                        },
                        {
                            title: 'Email',
                            data:'email'
                        },
                      ],
                      processing: true
                },
                contacts_table: null,
            }
        },
        components: {
          //Assessment
        },
        computed:{
            postalAddressReadonly: function() {
                /*
                if (this.readonly || this.email_user.postal_same_as_residential) {
                    return true;
                }
                */
                return true;
            },
            contactsURL: function(){
                // We don't need anything relating to organisations
                //return this.proposal != null ? helpers.add_endpoint_json(api_endpoints.organisations, this.proposal.org_applicant.id+'/contacts') : '';
                return ''
            },
            customerLabel: function() {
                let label = 'Applicant';
                if (this.customerType && this.customerType === 'holder') {
                    label = 'Holder';
                }
                return label;
            },

            //applicantType: function(){
            //    return this.proposal.applicant_type;
            //},
            // hasAssessorMode:function(){
            //     return this.proposal && this.proposal.assessor_mode.has_assessor_mode ? true : false;
            // },
        },
        methods:{
            fetchCountries:function (){
                let vm =this;
                vm.loading.push('fetching countries');
                vm.$http.get(api_endpoints.countries).then((response)=>{
                    vm.countries = response.body;
                    vm.loading.splice('fetching countries',1);
                },(response)=>{
                    //console.log(response);
                    vm.loading.splice('fetching countries',1);
                });
            },

            initialiseOrgContactTable: function(){
                let vm = this;
                //console.log("i am here")
                //if (vm.proposal && !vm.contacts_table_initialised){
                if (!vm.contacts_table_initialised){
                    // We don't need anything relating to organisations
                    //vm.contacts_options.ajax.url = helpers.add_endpoint_json(api_endpoints.organisations, vm.proposal.org_applicant.id + '/contacts');
                    vm.contacts_table = $('#'+vm.contacts_table_id).DataTable(vm.contacts_options);
                    vm.contacts_table_initialised = true;
                }
            },
        },
        mounted: function(){
            let vm=this;
            if (!vm.panelClickersInitialised){
            $('.panelClicker[data-toggle="collapse"]').on('click', function () {
                var chev = $(this).children()[0];
                window.setTimeout(function () {
                    $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
                },100);
            }); 
            vm.panelClickersInitialised = true;
            }
            this.$nextTick(() => {
                vm.initialiseOrgContactTable();
                
            });
        }
    }
</script>

<style lang="css" scoped>
</style>

