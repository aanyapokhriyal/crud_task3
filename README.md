# CRUD Task 3

A server-rendered CRUD application built with FastAPI, Jinja2 templates, and MySQL. Users can create accounts, log in, and manage user-detail records according to their role.

## Project files

| File or folder | Purpose |
| --- | --- |
| `main.py` | Creates the FastAPI application, serves static files, defines page and form routes, checks permissions, and renders templates or redirects. |
| `models.py` | Implements account registration and login verification, password hashing, JWT creation and validation, role permissions, date-of-birth validation, and CRUD database operations. |
| `mysql_connection.py` | Opens MySQL connections using the settings from `config.py`. |
| `config.py` | Loads `.env` values and defines the MySQL database settings and JWT configuration. |
| `crud_task3.sql` | Creates the database and tables and includes example SQL for assigning administrator roles. |
| `requirements.txt` | Lists the Python packages needed to run the application. |
| `templates/` | Contains the Jinja2 HTML pages returned by the routes. |
| `static/style.css` | Provides styles for success and error messages. |
| `env_format` | Example names for the environment variables the application expects. Create a `.env` file with real local values; do not put credentials in source control. |

### Templates

- `signup.html`: account creation form.
- `login.html`: login form and authentication messages.
- `dashboard.html`: navigation links shown according to the logged-in user's role.
- `register.html`: form for creating a user-detail record, with browser-side date-of-birth checks and optional ID search controls.
- `users.html`: table of records, with search results and role-dependent record actions.
- `edit.html`: form for editing a record.

## Requirements

- Python and the packages listed in `requirements.txt`.
- A running MySQL server.
- A MySQL database user with permission to create/use the application database and tables.
- A `.env` file containing `DB_PASSWORD` and `JWT_SECRET_KEY`.

## Setup and run (Windows PowerShell)

Run these commands from the project directory:

1. Create and activate a virtual environment if you do not already have one:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Virtual environments should be recreated if the project is moved, because their scripts can contain the old absolute path.

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. In MySQL Workbench or a MySQL client, run `crud_task3.sql` to create the `crud_task3` database and its tables.

4. Create a `.env` file in the project directory:

   ```env
   DB_PASSWORD=your_mysql_password
   JWT_SECRET_KEY=your_long_random_secret
   ```

   Generate a secret with:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   `config.py` connects to MySQL on `localhost` as `root`, uses the `crud_task3` database, and signs tokens with the configured JWT secret.

5. Start the development server:

   ```powershell
   python -m uvicorn main:app --reload
   ```

6. Visit <http://127.0.0.1:8000/signup> to create an account, then log in. Stop the server with **Ctrl+C**.

## User experience

1. A visitor opens the signup page, enters an email and password, and submits the form. The password form requires at least eight characters, including a lowercase letter, an uppercase letter, and a digit.
2. If the email is already registered, the signup page displays an error. Otherwise, the visitor sees a successful-signup message on the login page.
3. The user logs in with their email and password. On success, they are redirected to the dashboard.
4. The dashboard displays available actions for that account's role:
   - A `user` can add records.
   - An `admin` can add, view, update, and delete records.
   - A `superadmin` can view records.
5. A permitted user fills in the record form with a name, date of birth, course, and phone number. The application checks the date of birth in the browser and again on the server before inserting the record.
6. A permitted reader can view all records or search by record ID. Users with update or delete permission can use the corresponding actions in the record list.
7. The user follows the Logout link to clear the browser's authentication cookie and return to the login page.

## Backend request flow

1. **Route selection:** The browser sends an HTTP request to a path such as `/login` or `/register`. FastAPI dispatches it to the matching handler in `main.py`. Form submissions are parsed from URL-encoded form data.
2. **Authentication:** After a successful login, `models.py` creates a signed JWT containing the account ID (`sub`), role, and expiration. `main.py` places it in an HTTP-only `access_token` cookie. On later requests, `get_current_user` reads the bearer token or cookie, verifies the JWT signature and expiry, and returns the account ID and role.
3. **Authorization:** Protected handlers use `permission_checker` to obtain the role's allowed operations. `req` checks that the requested operation (create, read, update, or delete) is allowed. The templates also hide unavailable links and buttons; the backend checks are the enforcement point.
4. **Database access:** `models.py` calls `mysql_connection.get_connection()` and uses parameterized SQL to access MySQL. Account data is stored in `user_accounts`; CRUD records are stored in `user_details`.
5. **Response:** For page requests, the handler passes data and permissions to a Jinja template. For successful login, update, delete, and logout actions, it returns a redirect.

### Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/signup` | Show the signup form. |
| `POST` | `/signup` | Create an account. |
| `GET` | `/login` | Show the login form. |
| `POST` | `/login` | Verify credentials and set the authentication cookie. |
| `GET` | `/dashboard` | Show role-dependent navigation. |
| `GET`, `POST` | `/register` | Show and submit the new-record form. |
| `GET` | `/users` | List records. |
| `POST` | `/user` | Search for a record by ID. |
| `GET`, `POST` | `/update/{id}` | Show and submit the record-edit form. |
| `POST` | `/delete/{id}` | Delete a record. |
| `GET` | `/logout` | Delete the authentication cookie and redirect to login. |

## Database and roles

`crud_task3.sql` creates two tables:

- `user_accounts`: stores the account ID, unique email, hashed password, creation time, and role.
- `user_details`: stores the record ID, name, date of birth, course, phone, creator account ID, and timestamps. `created_by` references `user_accounts.id`.

Signup assigns the `user` role automatically. To give an account another role, update its row in MySQL, for example:

```sql
UPDATE user_accounts SET role = 'admin' WHERE email = 'admin@example.com';
```

The application defines permissions in `models.py`; use only the roles and permission mappings configured there.

## Implementation notes

- The browser-side date-of-birth validation is for immediate feedback. The server independently rejects dates before 1926, future dates, and dates that would make the person younger than 12.
- The login cookie is HTTP-only and expires after the configured token lifetime (currently 120 minutes). For production deployment, configure HTTPS and appropriate cookie security settings.
- Templates hide controls based on permissions, but each operation must also pass its backend permission check.
