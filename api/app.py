from flask import Flask
from flask_jsontools import jsonapi
from utils.queries import screened_stocks
from utils import ApiJSONEncoder

app = Flask(__name__)
app.json_encoder = ApiJSONEncoder


@app.route("/stocks", methods=["POST"])
@jsonapi
def stocks():
    result = screened_stocks()
    return result


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
