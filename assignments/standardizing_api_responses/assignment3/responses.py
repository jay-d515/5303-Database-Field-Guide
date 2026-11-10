from fastapi.responses import JSONResponse

def api_response(data=None, *, response_code=200, error_response=None,
                 total_size=None, offset=None,limit=None) -> dict:
    if isinstance(data, list):
        size = len(data)
    elif data is None:
        size = 0
    else:
        size = 1
        if total_size is None:
            total_size = 1
    
    body = {
        "response_code": response_code,
        "error_response": error_response,
        "data": data,
        "size": size,
        "total_size": total_size,
        "offset": offset,
        "limit": limit,
    }
    return JSONResponse(status_code=response_code, content=body)

def error_response(status_code, message, details=None):
    err = {"message": message}
    if details:
        err["details"] = details
    return api_response(None, response_code=status_code, error_response=err)