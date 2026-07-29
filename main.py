#main.py
from fastapi import FastAPI, Request,Form,Depends,HTTPException,Header
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import models
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.responses import RedirectResponse,HTMLResponse
from datetime import date
from starlette.exceptions import HTTPException as StarletteHTTPException


app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")    
templates = Jinja2Templates(directory="templates")

@app.get("/signup")
def show_signup_form(request:Request):
    #print(request)
    #print(Request)
    return templates.TemplateResponse(request=request,name="signup.html")

@app.post("/signup")
def signup_user(request:Request,email:str=Form(...),password:str=Form(...)):
    # print(email)
    # print(password)
    result= models.create_user_account(email, password)
    if result["message"] == "Email Taken":
        return templates.TemplateResponse(request=request, name="signup.html", context={"message": "Email already registered", "message_type": "error"})
    else:
        return templates.TemplateResponse(request=request, name="login.html", context={"message": "Signup successful! Please log in.", "message_type": "success"})
    
@app.get("/login")
def show_login_form(request:Request):
    return templates.TemplateResponse(request=request, name="login.html") 

@app.post("/login")
def login_user(request:Request,email:str =Form(...),password:str= Form(...)):
    result = models.verify_user(email, password)
    if result["message"] == "Login successful":
        access_token = models.create_access_token({"sub": str(result["id"]), "role":str(result["role"])})
        response = RedirectResponse("/dashboard", status_code=303)
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,#JavaScript cannot read this cookie.Only the browser automatically sends it with future requests.
            max_age= ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds, matches your expire time
        )
        return response                
    else:
        return templates.TemplateResponse(request=request, name="login.html", context={"message": result["message"], "message_type": result.get("message_type","")})

@app.get("/dashboard")
def dashboard(request: Request, current_user: dict = Depends(models.get_current_user)):
    if current_user is None:
        return RedirectResponse("/login", status_code=303) 
    permissions = models.role_permissions.get(current_user["role"], set()) #if role is found then return it or else empty set instead of crashing
    print("permissions:",permissions)
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"permissions": permissions})

@app.get("/register")
def show_register_form(request:Request,current_user: dict = Depends(models.get_current_user),
                       result=Depends(models.permission_checker)):
    if current_user is None:
            return RedirectResponse("/login", status_code=303)
    models.req(result["allowed_operations"], result["user"], "create")
    return templates.TemplateResponse(request=request, name="register.html",context={"permissions":result["allowed_operations"]})

@app.post("/register")
def register_user(request:Request, user_name:str =Form(...), dob:date= Form(...),
    course:str= Form(...),phone:str= Form(...), current_user: dict = Depends(models.get_current_user),
                       result=Depends(models.permission_checker)):
    if current_user is None:
        return RedirectResponse("/login", status_code=303)
    models.req(result["allowed_operations"], result["user"], "create")
    if not models.is_valid_dob(dob):
        return templates.TemplateResponse(request=request, name="register.html", context={"message": "Invalid date of birth", "message_type": "error"})
    created_by=int(current_user["sub"])
    models.insert_data(user_name,dob,course,phone,created_by)
    print(user_name,dob,course,phone)
    return templates.TemplateResponse(
        request=request,name="register.html",context={"message": "User registered successfully!", "message_type": "success","permissions":result["allowed_operations"]})
    
@app.get("/users")
def show_users(request: Request,current_user: dict = Depends(models.get_current_user),
                       result=Depends(models.permission_checker)):
    if current_user is None:
        return RedirectResponse("/login", status_code=303)
    models.req(result["allowed_operations"], result["user"], "read")
    users = models.get_all_users()
    permissions =models.role_permissions.get(current_user["role"], set())
    #print(users)
    return templates.TemplateResponse(request=request,name="users.html",context={"records": users,"permissions": permissions})

@app.post("/user")
def search_user(request: Request, id:int = Form(...),current_user: dict = Depends(models.get_current_user),
                       result=Depends(models.permission_checker)):
    models.req(result["allowed_operations"], result["user"], "read")
    user = models.get_user_by_id(id)
    if user:
        records = [user]    
    else:
        records = []
    return templates.TemplateResponse(request=request,name="users.html",context={"records": records, "searched_id": id})

@app.get("/update/{id}")
def edit_user(id: int, request: Request,current_user: dict = Depends(models.get_current_user),
                       result=Depends(models.permission_checker)):
    if current_user is None:
        return RedirectResponse("/login", status_code=303)
    models.req(result["allowed_operations"], result["user"], "update")
    user = models.get_user_by_id(id)
    #print("user",user)
    return templates.TemplateResponse(request=request, name="edit.html",context={"user": user})

@app.post("/update/{id}")
def update_user(id: int,user_name: str = Form(...),dob: date = Form(...),course: str = Form(...),
    phone: int = Form(...),
    #current_user: dict = Depends(models.get_current_user),
                       result=Depends(models.permission_checker)):
    models.req(result["allowed_operations"], result["user"], "update")
    models.update_user(id,user_name,dob,course,phone)
    return RedirectResponse("/users", status_code=303)

@app.post("/delete/{id}")
def delete_user_form(id: int,result=Depends(models.permission_checker)):
    models.req(result["allowed_operations"], result["user"], "delete")
    print(result["allowed_operations"])
    models.delete_user(id)
    return RedirectResponse("/users", status_code=303)

@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("access_token")
    return response 




# @app.exception_handler(StarletteHTTPException)
# def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
#     if exc.status_code == 401:
#         return RedirectResponse("/login", status_code=303)
#     if exc.status_code == 403:
#         html = f"""
#         <script>
#             alert("{exc.detail}");
#             window.location.href = "/dashboard";
#         </script>
#         """
#         return HTMLResponse(content=html, status_code=403)
#     raise exc