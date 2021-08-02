def mooringlicensing_processor(request):
    ret_dict = {}

    web_url = request.META.get('HTTP_HOST', None)
    ret_dict['PUBLIC_URL'] = web_url

    return ret_dict


