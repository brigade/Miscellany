from datadog import initialize, api
import sys
import os

options = {
	'api_key': os.environ['DD_API_KEY'],
	'app_key': os.environ['DD_APP_KEY']
}
initialize(**options)

class converter(object):
	
	graphs = []
	board = []
	board_type = ""
	widgets =[]
	template_variables = []
	title = "Converted Widget"
	@classmethod
	def getdash(cls, dash):
		# Get the dashboard or the screenboard associated with the ID in the arg
		# Set the dashboard type

		try:
			cls.board = api.Timeboard.get(dash)
		except:
			pass
		print cls.board_type

		if 'errors' in cls.board:
			print "Reference ## is not in your timeboards"
			try:
				cls.board = api.Screenboard.get(dash)
				cls.template_variables = cls.board['template_variables']
			except:
				pass
		else: 
			cls.board_type = "timeboard"
			return cls.board_type

		if 'errors' in cls.board:
			print "Reference ## is not in your screenboards"
		else:
			cls.board_type = "screenboard"
	@classmethod
	def delete_dash(cls, dash):
		print " \n If you have any warning above about outdated widget types, you should not delete the original dashboard. Follow the described procedure to properly convert the dashboard. \n"
		delete = raw_input("Do you want to delete the dash (Y/n): ")
		if delete =="Y" and cls.board_type == "screenboard":

			print "deleting screenboard: " + cls.board['board_title']
			api.Screenboard.delete(dash)
				
		elif delete == "Y" and cls.board_type == "timeboard":
			print "deleting timeboard " + cls.board['dash']['title']
			api.Timeboard.delete(dash)

		elif delete == "n":
			print "No further action needed"

		else:
			print "Please select Y or n."
			cls.delete_dash(dash)

	@classmethod
	def widget_transform(cls):
		# Transform the widget list so they are properly formatted 
		# Take off the Screenboard widgets not available in the Timeboards 
		# Returns the list of the different widgets

		if cls.board_type == "screenboard":
			## Get the widgets
			finaltimeboard_widgets=[]
			screenwidgets = cls.board['widgets']
			## Filter the illegal widgets
			forbidden_widget = ['free_text','alert_value','check_status','event_timeline','event_stream','image','note','alert_graph','iframe']
			tmp = [screenwidgets[x]['type'] not in forbidden_widget for x in range(len(screenwidgets))]
			
			## Add the valid widgets
			for x in range(len(tmp)):
				if tmp[x]:
					finaltimeboard_widgets.append(screenwidgets[x])
			return finaltimeboard_widgets

		else:
			return cls.board['dash']['graphs']

		## Convert the widgets
	@classmethod
	def convert_s2t(cls, widgets, old_service = None, new_service = None):
		# Function to convert Screenboard to Timeboard.
		# Takes the widgets as input and output the widgets properly formatted.
		# Appens an additionnal attribute for the hostmap.
		# no output, just tranforms the cls.graphs
		
		for i in range(len(widgets)):

			if 'tile_def' in widgets[i]:
				if 'conditional_formats' not in widgets[i]['tile_def']['requests'][0]:
					widgets[i]['tile_def']['requests'][0]['conditional_formats'] = []
			else: 
				widgets[i]['tile_def'] = 'outdated'
				print "One of the widgets' type is outdated and won't be ported.\n To solve this, just click on edit the dashboard, open a widget, hit done and save the dashboard.\n Then run the script again."
				print widgets[i]


			# Replace service name in metrics
			if old_service and new_service:
				for request in widgets[i]['tile_def']['requests']:
					request['q'] = request['q'].replace(old_service, new_service)

			if widgets[i]['type'] == 'hostmap':

				cls.graphs.append({
					"definition":{
					"style": widgets[i]['tile_def']['style'],
					"requests":widgets[i]['tile_def']['requests'],
					"viz":widgets[i]['type'],
					},
					"title":  widgets[i]['title_text']
				})
			elif widgets[i]['tile_def'] == 'outdated':
				pass
			else:			
				cls.graphs.append({
					"definition":{
					"events": [],
					"requests":widgets[i]['tile_def']['requests'],
					"viz":widgets[i]['type'],
					},
					"title": widgets[i]['title_text']
				})

		## Convert the widgets
	@classmethod
	def convert_t2s(cls, graphs, old_service = None, new_service = None):
		# Function to convert Timeboard to Screenboard.
		# Takes the widgets as input and output the widgets properly formatted.
		# pos_x, pos_y and tmp_y assure the right position of the widgets
		# margin, height and width are hardcoded values representing the default size of the widgets
		# hostmap, heatmap and distribution have specific treatment as their payload is different on a TB and on a SB

		pos_x = 0
		pos_y = 0
		height = 13
		width =  47
		margin = 5
		tmp_y = 0
		for i in range(len(graphs)):

			# Replace service name in metrics
			if old_service and new_service:
				for request in graphs[i]['definition']['requests']:
					request['q'] = request['q'].replace(old_service, new_service)

			if i % 2 == 0 and i != 0:
				pos_x = 0
				tmp_y = pos_y

			elif i % 2 == 1 and i != 0:
				tmp_y = pos_y
				pos_y = pos_y + height + margin
				pos_x = width + margin

			if 'viz' not in graphs[i]['definition']:
				print "One of the widgets' type is outdated and won't be ported.\n To solve this, just click on edit the dashboard, open a widget, hit done and save the dashboard.\n Then run the script again."
				graphs[i]['definition']['viz'] = "timeseries" # Defaults to timeseries to avoid having an empty screenboard.
				print graphs[i] # If the vizualisation is a QVW, the user will have to open the original dashboard, Open and Save the faulty widget.

			if graphs[i]['definition']['viz'] not in ["hostmap","distribution","heatmap"]:
				cls.widgets.append({
					'height': height, 
					'width': width, 
					'timeframe': '4h',
					'x' : pos_x,
					'y' : tmp_y,
					"tile_def":{
					"requests":graphs[i]['definition']['requests'],
					"viz":graphs[i]['definition']['viz'],
					},
					"title_text": graphs[i]['title'],
					"title": True,
					"type":graphs[i]['definition']['viz']
				})

			elif graphs[i]['definition']['viz'] == "heatmap" or graphs[i]['definition']['viz'] == "distribution":
				graphs[i]['definition']['requests'][0]['type'] = 'line'
				graphs[i]['definition']['requests'][0]['aggregator'] = 'avg'
				cls.widgets.append({
					'height': height, 
					'width': width, 
					'timeframe': '4h',
					'x' : pos_x,
					'y' : tmp_y,
					"tile_def":{
					"requests":graphs[i]['definition']['requests'],
					"viz":graphs[i]['definition']['viz'],
					},
					"title_text": graphs[i]['title'],
					"title": True,
					"type":"timeseries"
				})

			elif graphs[i]['definition']['viz'] == "hostmap":
				cls.widgets.append({
					'height': height, 
					'width': width, 
					'timeframe': '4h',
					'x' : pos_x,
					'y' : tmp_y,
					"tile_def":graphs[i]['definition'],
					"title_text": graphs[i]['title'],
					"title": True,
					"type":"hostmap"
				})

	@classmethod
	def main(cls, dash, old_service = None, new_service = None):
		# Main fuction to fetch the dashboards, extract the widgets, transform the widgets and push the result
		# Takes the dash to convert as an input
		# Outputs the url of the new dash

		cls.getdash(dash)
		if cls.board_type == "screenboard":
			widgets = cls.widget_transform()
			cls.convert_s2t(widgets, old_service, new_service)
			output = api.Timeboard.create(title=cls.title, description='description', graphs=cls.graphs, template_variables=cls.template_variables, read_only=False)
			cls.delete_dash(dash)
			print 'Your new Timeboard is available at: http://app.datadoghq.com'+output['url']

		else:
			graphs = cls.widget_transform()
			cls.convert_t2s(graphs, old_service, new_service)
			output = api.Screenboard.create(board_title=cls.title, description='description', widgets=cls.widgets, template_variables=cls.template_variables)			
			cls.delete_dash(dash)			
			print "Your new Screenboard is available at: http://app.datadoghq.com/screen/" + str(output['id'])
if len(sys.argv) == 4:
	converter().main(sys.argv[1], sys.argv[2], sys.argv[3])
else:
	converter().main(sys.argv[1])

