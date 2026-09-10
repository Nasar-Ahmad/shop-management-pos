# Shop Management POS

A professional desktop-based Shop Management and Point of Sale (POS) application built with **Python, CustomTkinter, and SQLite**.

The application is designed for small shops and businesses that need a simple offline solution for product management, billing, customer records, credit/udhar management, sales history, and reports.

## ✨ Features

- 🔐 Admin login and authentication
- 🧾 Create and manage customer bills
- 🔎 Product-code based product lookup
- 💰 Manual bill-price adjustment
- 🏷️ Item-level discounts
- 👥 Customer management
- 📋 Previous bill and sales history
- 💳 Udhar / Credit management
- 💵 Receive and track credit payments
- 📊 Sales reports
- 📅 Date-based sales searching
- 💾 SQLite local database
- 🔄 Database backup support
- 🌙 Dark and light interface
- 🖥️ Offline desktop application

## 🛠️ Technology Stack

- **Python**
- **CustomTkinter**
- **SQLite**
- **Tkinter**

## 📁 Project Structure

```text
ShopManagement/
│
├── Main.py
├── database.py
├── .gitignore
│
├── Database/
│   └── shop.db
│
└── Bills/
The local SQLite database and generated bills are excluded from the public Git repository.

Requirements
Windows 10 or Windows 11
Python 3.10 or newer
Git (only required for development)
Installation
1. Clone the repository
git clone https://github.com/Nasar-Ahmad/shop-management-pos.git
2. Open the project
cd shop-management-pos
3. Install CustomTkinter
pip install customtkinter
4. Run the application
python Main.py
Default Login

For the initial/demo installation:

Username: admin
Password: admin123

Change the administrator credentials from the application's Settings section after first login.

Data Storage

The application uses SQLite for local data storage.

Customer records, products, sales, bills, and credit/payment information are stored locally on the computer running the application.

The database is intentionally excluded from this public repository to prevent private business/customer data from being published.

Privacy

Do not upload real customer information, phone numbers, sales records, passwords, or other private business data to this repository.

Project Status

Active Development

The project is being developed as an offline desktop Shop Management and POS application.

Contributing

Contributions, suggestions, bug reports, and improvements are welcome.

Fork the repository.
Create a new branch.
Make your changes.
Test the application.
Submit a pull request.
Bug Reports

If you find a bug, please open a GitHub Issue and provide:

A clear description of the problem
Steps to reproduce it
Expected behavior
Actual behavior
Relevant error messages

Please do not include private customer or business information in bug reports.

License

This project is open source and will be distributed under the MIT License.

See the LICENSE file for details.

If you find this project useful, consider giving the repository a star.

Built with Python for simple and practical offline shop management.


Phir **Ctrl + S** karo.

### Step 7 — Check karo

Terminal mein:

```powershell
git status