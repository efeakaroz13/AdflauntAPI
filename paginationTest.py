import redis
import flask 

app = flask.Flask(__name__)
r = redis.Redis()



@app.route("/")
def index():
	results = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
	p = flask.request.args.get("p")

	if p == None:
		p = 1
	else:
		p = int(p)
	results_data = {
		"results":results[:p*5][5*(p-1):]
	}
	return results_data


app.run(debug=True,port=3000)
