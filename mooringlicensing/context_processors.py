def mooringlicensing_processor(request):
    ret_dict = {}

    web_url = request.META.get('HTTP_HOST', None)

    return {'public_url': web_url}


