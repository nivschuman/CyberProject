# Flask Security Vulnerabilities Demo
[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This project is a Python Flask web application created as part of a cybersecurity learning exercise.  
It demonstrates common security vulnerabilities found in web applications and how to fix them.

---

## Project Structure

- `master` branch: Contains the original Flask application with intentional security vulnerabilities for educational purposes.
- `security` branch: Contains the improved Flask application with the vulnerabilities addressed and fixed.

---

## Vulnerabilities Demonstrated

The `master` branch intentionally includes some of the following common security issues:

- **SQL Injection**: Non sanitized user input used directly in SQL queries.
- **Cross-Site Scripting (XSS)**: User input rendered in HTML without proper escaping.
- **Insecure Session Management**: Weak or missing session protection.
- **Lack Of Content Security Policy**: Absense of content security policy header.
- **Hardcoded Secrets**: Use of plaintext secrets or keys in the source code.
- **CSRF Vulnerabilities**: Missing CSRF tokens on form submissions.

---

## Fixes Applied

The `security` branch contains corrections such as:

- Use of parameterized queries to prevent SQL injection.
- Proper escaping or sanitization of user-generated content to mitigate XSS.
- Secure session handling with Flask’s built-in session management best practices.
- Addition of content security policy header.
- Proper management of secrets.
- Implementation of CSRF protection using Flask-WTF.

---

## How to Use

1. Clone the repository:

       git clone https://github.com/nivschuman/CyberProject.git

2. To explore the vulnerable version:

       git checkout master

3. To explore the fixed version:

       git checkout security

4. Install dependencies:

       pip install -r requirements.txt

5. Run the app (choose one):

   - Using Python directly:
     
         python main.py

   - Using Flask CLI:

         export FLASK_APP=main.py
         flask run

---

## Disclaimer

This project is for educational purposes only. Do not use the vulnerable code in production environments.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
