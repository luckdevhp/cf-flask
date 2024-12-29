import requests
import configparser
import time
import os
from flask import Blueprint, request, jsonify, render_template, send_file

# Blueprint setup
add_domains = Blueprint('add_domains', __name__, template_folder='templates')

# Load API token and account details from configurations.ini file
config = configparser.ConfigParser()
config.read('configurations.ini')

api_token = config.get('cloudflare', 'api_token')
account_id = config.get('cloudflare', 'account_id')  # Add your Cloudflare account ID in configurations.ini

# Headers for Cloudflare API
headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}

@add_domains.route('/', methods=['GET', 'POST'])
def manage_domains():
    if request.method == 'POST':
        domains_input = request.form.get('domains')
        if not domains_input:
            return jsonify({"error": "No domains provided"}), 400

        # Parse domains from textarea input
        domains = [domain.strip() for domain in domains_input.splitlines() if domain.strip()]
        results = []
        logs = []

        for domain in domains:
            domain_data = {
                "name": domain,
                "account": {"id": account_id},
                "jump_start": True
            }

            try:
                response = requests.post('https://api.cloudflare.com/client/v4/zones', headers=headers, json=domain_data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        zone_id = result['result']['id']
                        name_servers = result['result']['name_servers']
                        logs.append(f"Domain {domain} added successfully.")

                        # Configure Always Use HTTPS
                        always_https_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/settings/always_use_https'
                        https_response = requests.patch(always_https_url, headers=headers, json={"value": "on"})

                        # Append result
                        results.append({"domain": domain, "name_servers": name_servers})
                    else:
                        # Trích xuất và hiển thị message từ lỗi
                        error_message = result.get('errors', [{}])[0].get('message', 'Unknown error')
                        logs.append(f"Failed to add domain: {error_message}")
                else:
                    # Xử lý cho trường hợp lỗi HTTP khác
                    error_response = response.json()
                    error_message = error_response.get('errors', [{}])[0].get('message', 'Unknown error')
                    logs.append(f"Error adding domain: {error_message}")

            except requests.exceptions.RequestException as e:
                logs.append(f"Exception adding domain {domain}: {str(e)}")

            # Avoid hitting API rate limits
            time.sleep(1)

        # Save results to CSV
        output_file = os.path.join('static', 'added_domains.csv')
        if results:
            with open(output_file, 'w') as file:
                file.write("Domain,Name Server\n")
                for result in results:
                    file.write(f"{result['domain']},{','.join(result['name_servers'])}\n")

        return jsonify({"logs": logs, "csv_file":output_file if results else None})
    
    return render_template('add_domains.html')