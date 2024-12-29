from flask import Flask, render_template
from app.add_domains import add_domains
from app.redirect_rules import redirect_rules

def create_app():
    # Tạo ứng dụng Flask
    app = Flask(__name__, static_folder='static')

    # Đăng ký các Blueprint
    app.register_blueprint(add_domains, url_prefix='/add-domains')
    app.register_blueprint(redirect_rules, url_prefix='/redirect-rules')

    # Định nghĩa route gốc
    @app.route('/')
    def home():
        return render_template('index.html')

    return app