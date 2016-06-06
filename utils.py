from aiohttp import web

def redirect(request, router_name):
    url = request.app.router[router_name].url()
    raise web.HTTPFound(url)

async def check_for_winner(data=None):
	length = len(data)
	ranges = range(length)

	# Check horizontal values
	for row in data:
		if row[0] and row[1:] == row[:-1]:
			return row[0]

	# Check vertical values
	for j in ranges:
		if data[0][j]:
			row = []
			for i in ranges:
				row.append(data[j][i])
			if row[1:] == row[:-1]:
				return row[0]

	# Check diagonal values
	# Top-right to bottom-left
	if data[0][0]:
		row = [rows[i] for i, rows in enumerate(data)]
		if row[1:] == row[:-1]:
			return row[0]

	# Top-left to bottom-right
	if data[0][length-1]:
		row = [rows[-i-1] for i, rows in enumerate(data)]
		if row[1:] == row[:-1]:
			return row[0]	

	return 0
