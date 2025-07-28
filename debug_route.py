from flask import jsonify


@app.route('/debug/routes')
def debug_routes():
    output = [f"{rule.endpoint}: {rule.rule}" for rule in app.url_map.iter_rules()]
    return jsonify({"routes": sorted(output)})
