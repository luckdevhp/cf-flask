from flask import Blueprint, render_template, request, flash, jsonify, Response
import requests
import configparser
import time

# Load API token từ configurations.ini
config = configparser.ConfigParser()
config.read('configurations.ini')
api_token = config.get('cloudflare', 'api_token')

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

# Blueprint setup
redirect_rules = Blueprint('redirect_rules', __name__, template_folder='templates')

# Hàm lấy Zone ID
def get_zone_id(session, domain):
    url = f"https://api.cloudflare.com/client/v4/zones?name={domain}"
    response = session.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            return result['result'][0]['id']
    return None

# Hàm xóa Page Rules hiện tại
def delete_existing_rules(session, page_rules_url):
    response = session.get(page_rules_url, headers=headers)
    if response.status_code == 200:
        return response.json().get('result', [])
    return []

# Hàm tạo Page Rule mới
def create_page_rule(session, page_rules_url, rule):
    response = session.post(page_rules_url, headers=headers, json=rule)
    return response.status_code == 200

def generate_progress(domains, target, status_code):
    steps = len(domains)  # Tổng số bước xử lý là số lượng domain
    for i, domain in enumerate(domains):
        # Giả lập một số thời gian xử lý cho mỗi domain
        time.sleep(1)  # Giả lập thời gian chờ
        yield f"data: {i+1}/{steps} - Redirecting {domain} to {target}\n\n"  # Cập nhật tiến độ
    yield "data: Complete\n\n"  # Khi hoàn thành

@redirect_rules.route('/progress')
def progress():
    domains = request.args.get('domains').split(',')
    target = request.args.get('target')
    status_code = request.args.get('status_code', 301)
    return Response(generate_progress(domains, target, status_code), mimetype='text/event-stream')

@redirect_rules.route('/', methods=['GET', 'POST'])
def manage_redirect():
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        domains = request.form.get('domains').strip().splitlines()
        target = request.form.get('target_domain').strip()
        path = request.form.get('path', '$1')
        status_code = int(request.form.get('status_code', 301))

        if not domains or not target:
            flash("Please provide both domains and a target domain.", "error")
            return jsonify({'logs': ['Please provide both domains and a target domain.']})

        results = []
        with requests.Session() as session:
            for domain in domains:
                zone_id = get_zone_id(session, domain)
                if not zone_id:
                    results.append(f"Failed to get Zone ID for {domain}")
                    continue

                # URL để quản lý Page Rules
                page_rules_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/pagerules"
                existing_rules = delete_existing_rules(session, page_rules_url)
                for rule in existing_rules:
                    session.delete(f"{page_rules_url}/{rule['id']}", headers=headers)

                # Tạo Page Rules mới
                rules = [
                    {
                        "targets": [{"target": "url", "constraint": {"operator": "matches", "value": f"https://{domain}/*"}}],
                        "actions": [{"id": "forwarding_url", "value": {"url": f"https://{target}/{path}", "status_code": status_code}}],
                        "priority": 1,
                        "status": "active"
                    },
                    {
                        "targets": [{"target": "url", "constraint": {"operator": "matches", "value": f"https://www.{domain}/*"}}],
                        "actions": [{"id": "forwarding_url", "value": {"url": f"https://{target}/{path}", "status_code": status_code}}],
                        "priority": 1,
                        "status": "active"
                    }
                ]
                for rule in rules:
                    success = create_page_rule(session, page_rules_url, rule)
                    results.append(f"Redirect created for {domain}" if success else f"Failed to create redirect for {domain}")

        # Trả về kết quả dưới dạng JSON
        return jsonify({
            'logs': results
        })

    return render_template('redirect_rules.html')
