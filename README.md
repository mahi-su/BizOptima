# BizOptima

BizOptima is a Flask + Scikit-learn web app for business profit forecasting, risk analysis, what-if planning, and report exports.

## Run on Windows

1. Double-click `start_windows.bat`.
2. Wait for dependencies and the ML model to prepare.
3. Open `http://127.0.0.1:5000`.
4. Create a new account from the signup page and sign in.

## Open in VS Code

Double-click `open_in_vscode.bat`, or open this folder directly in VS Code.

## Project Structure

- `backend/` - Flask app, API routes, database models, ML model training.
- `frontend/templates/` - Landing, signin, signup, and dashboard pages.
- `frontend/static/` - CSS and JavaScript.

Each user account has its own saved prediction history and exports.
