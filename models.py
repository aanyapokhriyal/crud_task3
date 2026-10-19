#from config import (IEX_API_URL,IEX_API_KEY)
import mysql_connection
#from mysql_connection import get_connection
from fastapi import Depends,Request, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from jose import jwt,JWTError
from datetime import datetime, timedelta, timezone,date
from config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login",auto_error=False)

def create_user_account(email, password):
      conn=mysql_connection.get_connection()
      cursor=conn.cursor()
      query=""" select email from user_accounts where email= %s """
      cursor.execute(query,(email,))
      user = cursor.fetchone()
      if user:
        cursor.close()
        conn.close()
        return {"message": "Email Taken"}
      else:
        hashed_password = password_hash.hash(password)
        query=""" insert into user_accounts (email,hashed_password,role)
        values (%s,%s,%s) """
        values=(email,hashed_password,"user")
        print(values)
        cursor.execute(query,values)
        conn.commit()
        cursor.close()
        conn.close()
        return {"message": "Successful "}
      
def verify_user(email, password):
    conn = mysql_connection.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """ SELECT email, hashed_password, id, role FROM user_accounts
        WHERE email = %s """
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if not user:
            return {"message": "User not found", "message_type": "error"}
        if password_hash.verify(password, user["hashed_password"]):
            return {"message": "Login successful","id": user["id"],"message_type": "success","role": user["role"] }
        return {"message": "Invalid password","message_type": "error"}

    finally:
        cursor.close()
        conn.close()

IST = timezone(timedelta(hours=5, minutes=30))

def create_access_token(data: dict):
    print("data:",data)
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    #print("Expire (UTC):", expire)
    print("Expire (IST):", expire.astimezone(IST))
    to_encode.update({"exp": expire})
    #print(to_encode)
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    #print("Header token:", token)
    if token is None:
        token = request.cookies.get("access_token")
        #print("Cookie token:", token)
    if token is None:
        #print("No token found anywhere — returning None")
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        #print("payload", payload)
        return {"sub":payload["sub"],"role":payload["role"]}
    except JWTError:
        return None
    
def insert_data(user_name,dob,course,phone,created_by):
    conn= mysql_connection.get_connection()
    cursor= conn.cursor()

    query= """ insert into user_details (user_name,dob,course,phone,created_by)
    values (%s,%s,%s,%s,%s) """

    values=(user_name,dob,course,phone,created_by)

    cursor.execute(query,values)
    conn.commit()
    cursor.close()
    conn.close()

def get_all_users():
        conn= mysql_connection.get_connection()
        cursor= conn.cursor(dictionary=True)
        query= """select * from user_details"""
        cursor.execute(query)
        users = cursor.fetchall()
    
        cursor.close()
        conn.close()
        return users

def get_user_by_id(id):
      conn=mysql_connection.get_connection()
      cursor=conn.cursor(dictionary=True)
      query=""" select * from user_details where id= %s """

      cursor.execute(query,(id,))
      user = cursor.fetchone()

      cursor.close()
      conn.close()
      return user
    
def update_user(id,user_name,dob,course,phone):
    conn=mysql_connection.get_connection()
    cursor=conn.cursor()
    query="""update user_details set user_name=%s,dob=%s,course=%s,phone=%s 
    where id=%s """

    values=(user_name,dob,course,phone,id)

    cursor.execute(query,values)
    conn.commit() 
    print(cursor.rowcount) # Debug: should print 1 if a row was updated

    cursor.close()
    conn.close()
      
def delete_user(id):
      conn=mysql_connection.get_connection()
      cursor=conn.cursor()
      query=""" delete from user_details where id= %s """
      cursor.execute(query,(id,))
      conn.commit()
      cursor.close()
      conn.close()
      



# def require_permission(operation: str):
#     def permission_checker(current_user=Depends(get_current_user)):
#         if current_user is None:
#             raise HTTPException(status_code=401, detail="Not authenticated")
#         allowed_operations = role_permissions.get(current_user["role"])
#         print("allowed_operations:",allowed_operations)
#         if allowed_operations is None:
#             raise HTTPException(status_code=403, detail="Role not recognized")
#         if operation not in allowed_operations:
#             raise HTTPException(status_code=403, detail="You are not authorised to perform this action")
#         return current_user
#     return permission_checker


role_permissions = {
    "superadmin": {"read"},
    "admin": {"create", "read", "update", "delete"},
    "user": {"create"}
}

def  permission_checker(current_user=Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    allowed_operations = role_permissions.get(current_user["role"])
    #print("allowed_operations:",allowed_operations)
    if allowed_operations is None:
        raise HTTPException(status_code=403, detail="Role not recognized")
    return {"user": current_user, "allowed_operations": allowed_operations}
    
def req(allowed_operations,user,operation:str):
    if operation not in allowed_operations:
        raise HTTPException(status_code=403, detail="You are not authorised to perform this action")
    return user

def is_valid_dob(dob: date):
    today = date.today()
    
    if dob.year < 1926:
        print(dob.year)
        return False
    if dob > today:
        return False
    
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    
    if age < 12:
        return False
    
    return True
