//	Copyright 2016 Paul Broadhead
//	Contact: pjbroad@twinmoons.org.uk
//
//	This file is part of pi_sensors.
//
//	pi_sensors is free software: you can redistribute it and/or modify
//	it under the terms of the GNU General Public License as published by
//	the Free Software Foundation, either version 3 of the License, or
//	(at your option) any later version.
//
//	pi_sensors is distributed in the hope that it will be useful,
//	but WITHOUT ANY WARRANTY; without even the implied warranty of
//	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//	GNU General Public License for more details.
//
//	You should have received a copy of the GNU General Public License
//	along with pi_sensors.  If not, see <http://www.gnu.org/licenses/>.

"use strict";

var pi_sensors_readings = pi_sensors_readings ||
{
	sensor_types: [],
	sensor_type_index: 0,
	sensor_info: null,
	current_room: null,
	the_graph: null,

	init_page: function()
	{
		var timer_id = null;
		var self = this;
		$( "#datepicker" ).datepicker({dateFormat: "D M d yy", changeMonth: true, changeYear: true});
		$( "#datepicker" ).datepicker( "setDate", new Date());
		window.onresize = function()
		{
			if (timer_id !== null)
				clearTimeout(timer_id);
			timer_id = setTimeout(self.update.bind(self), 100);
		};
		this.get_rooms();
	},

	build_tabs: function()
	{
		function handler(response)
		{
			if (("data" in response) && (response.data != null) && response.data.length)
			{
				var ul_h = document.getElementById("sensor_tabs");
				var sensors = response.data;
				var self = this;
				var tab_id = 0;
				var next_tab_id = null;
				this.sensor_types = [];
				while( ul_h.firstChild )
					ul_h.removeChild( ul_h.firstChild );
				for (var i=0; i<sensors.length; i++)
				{
					var tab = {"type":sensors[i], "name":sensors[i][0].toUpperCase()};
					var li = document.createElement("li");
					tab.id = "tab_id" + tab_id++;
					li.appendChild(document.createTextNode(tab.name));
					li.setAttribute("id", tab.id);
					li.onclick = function(e) { self.set_tab(e.target.id); };
					ul_h.appendChild(li);
					if (this.sensor_info && (this.sensor_info.name == tab.name))
						next_tab_id = tab.id;
					this.sensor_types.push(tab);
				}
				this.sensor_info = null;
				this.set_tab( (next_tab_id) ?next_tab_id :this.sensor_types[0].id );
			}
		}
		var url = pi_sensors_config.paths["api"] + "/" + this.current_room + "/distinct/type";
		request_common.get_data(url, handler.bind(this));
	},

	get_rooms: function()
	{
		function fill_select(response)
		{
			if (("data" in response) && (response.data != null))
			{
				var rooms = response.data;
				var sel = document.getElementById('rooms');
				for (var i = 0; i < rooms.length; i++)
				{
					var opt = document.createElement('option');
					opt.innerHTML = rooms[i];
					opt.value = rooms[i];
					sel.appendChild(opt);
				}
				if (rooms.length > 0)
				{
					this.current_room = rooms[0];
					this.build_tabs();
				}
			}
		}
		var url = pi_sensors_config.paths["api"] + "/distinct/room";
		request_common.get_data(url, fill_select.bind(this));
	},

	change_room: function()
	{
		this.current_room = document.forms.controls.room.value.toLowerCase();
		this.build_tabs();
	},

	change_day: function(delta)
	{
		var new_date = null;
		if (delta == 0)
			new_date = new Date();
		else
		{
			new_date = $( "#datepicker" ).datepicker( "getDate" );
			new_date.setDate(new_date.getDate() + delta);
		}
		$( "#datepicker" ).datepicker( "setDate", new_date);
		this.update();
	},

	update: function()
	{
		error_message.clear();
		if (this.current_room)
			this.current(this.current_room);
		else
			error_message.display("No readings");
	},

	set_tab: function(tab_id)
	{
		if (this.sensor_info)
			document.getElementById(this.sensor_info.id).className = "null";
		for (var i=0; i<this.sensor_types.length; i++)
			if (tab_id === this.sensor_types[i].id)
			{
				document.getElementById(tab_id).className = "selected";
				this.sensor_info = this.sensor_types[i];
				this.update();
				break;
			}
	},

	toggle_last_readings: function()
	{
		var last_readings_h = document.getElementById("last_readings")
		if (document.getElementById("show_last_readings").checked)
			last_readings_h.style.display = 'inline';
		else
			last_readings_h.style.display = 'none';
		this.update();
	},

	current: function(room)
	{
		function display_last(response)
		{
			var last_readings_h = document.getElementById("last_readings")
			var show_outdated_warning = true;
			if (("data" in response) && (response.data.length > 0))
			{
				var first_reading = response.data[0].record;
				var epoch_now = new Date().getTime();
				var the_date = new Date(first_reading.epoch * 1000);
				var thetext = "<h2>" + this.formated_date(the_date) + " " +
					("0" + the_date.getHours()).slice(-2) + ":" + ("0" + the_date.getMinutes()).slice(-2);
				for (var device in response.data)
				{
					var reading = response.data[device].record;
					thetext += " | " + response.data[device].device + ": " + reading.record.value;
					if ("units" in reading.record && reading.record.units)
						thetext += " " + reading.record.units;
				}
				last_readings_h.innerHTML = thetext + "</h2>";
				if ((epoch_now/1000.0 - first_reading.epoch) < 20*60)
					show_outdated_warning = false;
			}
			else
				last_readings_h.innerHTML = "<h2>No recent data</h2>";
			if (show_outdated_warning)
				document.getElementById("warning_message").innerHTML = "<span class='alert'>OUTDATED</span>";
			else
				document.getElementById("warning_message").innerHTML = "";
		}
		var start_date = integer_date.date2yyyymmdd(new Date());
		var url = pi_sensors_config.paths["api"] + "/" + room + "/" + this.sensor_info.type + "/latest";
		var start_date = integer_date.date2yyyymmdd($( "#datepicker" ).datepicker( "getDate" ));
		this.graph(start_date, this.current_room);
		request_common.get_data(url, display_last.bind(this));
	},

	graph: function(start_date, room)
	{
		function display_graph(response)
		{
			var the_columns = [];
			var data = response.data;
			var use_log = document.getElementById("use_logscale").checked;
			var show_full = document.getElementById("show_full").checked;

			var the_times = ['x'];
			var the_device = (data.length) ?data[0].record.device : "";
			var min_value = (data.length) ?data[0].record.value : 0;
			for (var i=0; i<data.length; i++)
			{
				if (data[i].record.value < min_value)
					min_value = data[i].record.value;
				if (show_full && ("values" in data[i].record))
				{
					for (var value_name in data[i].record.values)
					{
						var the_value = data[i].record.values[value_name];
						if (the_value < min_value)
							min_value = the_value;
					}
				}
				if (data[i].record.device != the_device)
					continue;
				var the_date = new Date(data[i].epoch * 1000);
				the_times.push(("0" + the_date.getHours()).slice(-2) + ":" + ("0" + the_date.getMinutes()).slice(-2));
			}
			the_columns.push(the_times);

			var the_data = {};
			for (var i=0; i<data.length; i++)
			{
				var device = data[i].record.device;
				if (show_full && ("values" in data[i].record))
				{
					for (var value_name in data[i].record.values)
					{
						var the_name = device + "." + value_name;
						var the_value = data[i].record.values[value_name];
						if (use_log)
							the_value = Math.log10(the_value + (1 - min_value));
						if (!(the_name in the_data))
							the_data[the_name] = [the_name];
						the_data[the_name].push(the_value);
					}
				}
				else
				{
					var the_value = data[i].record.value;
					if (use_log)
						the_value = Math.log10(the_value + (1 - min_value));
					if (!(device in the_data))
						the_data[device] = [device];
					the_data[device].push(the_value);
				}
			}
			for (var key in the_data)
				the_columns.push(the_data[key]);

			var page_width = Math.min(window.innerWidth, window.outerWidth) - side_bar.get_width();
			var page_height = Math.min(window.innerHeight, window.outerHeight);
			var graph_height = page_height - document.getElementById("non_graph").offsetHeight;
			if (this.the_graph)
				this.the_graph.destroy();
			this.the_graph = c3.generate
			({
				bindto: '#readings_graph',
				size: { height:graph_height-20, width:page_width-40 },
				data: { x:'x', xFormat:'%H:%M', columns:the_columns },
				axis: { x:{ type:'timeseries', label: {show:false}, tick:{ format:'%H:%M' } },
					y:{ tick: { format: d3.format(".1f") }}}
			});
			var title = this.sensor_info.type[0].toUpperCase() + this.sensor_info.type.substring(1);
			d3.select("#readings_graph svg").append("text").attr("x", page_width/2).attr("y", 0).attr('class', 'graph_title').text(title);
		}
		var url = pi_sensors_config.paths["api"] + "/" + room + "/" + this.sensor_info.type + "/get_readings" + "?start_date=" + start_date;
		request_common.get_data(url, display_graph.bind(this));
	},

	formated_date: function(thedate)
	{
		var days = [ "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" ];
		var months = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" ];
		return days[thedate.getDay()] + " " + thedate.getDate() + " " + months[thedate.getMonth()];
	},

	toggleFullScreen: function ()
	{
		// Thanks: http://www.html5rocks.com/en/mobile/fullscreen/
		var doc = window.document;
		var docEl = doc.documentElement;
		var requestFullScreen = docEl.requestFullscreen || docEl.mozRequestFullScreen || docEl.webkitRequestFullScreen || docEl.msRequestFullscreen;
		var cancelFullScreen = doc.exitFullscreen || doc.mozCancelFullScreen || doc.webkitExitFullscreen || doc.msExitFullscreen;
		if(!doc.fullscreenElement && !doc.mozFullScreenElement && !doc.webkitFullscreenElement && !doc.msFullscreenElement)
			requestFullScreen.call(docEl);
		else
			cancelFullScreen.call(doc);
	},
}


var side_bar = side_bar ||
{
	// based on http://www.w3schools.com/howto/howto_js_sidenav.asp

	width: 200,
	current_width: 0,

	get_width: function()
	{
		return this.current_width;
	},

	disable: function()
	{
		if (this.get_width())
		{
			this.close();
			this.reenable = true;
		}
	},

	enable: function()
	{
		if (this.reenable)
		{
			this.open();
			this.reenable = false;
		}
	},

	open: function()
	{
		var width_px = this.width + "px";
		document.getElementById("side_bar_panel").style.width = width_px;
		document.getElementById("main_panel").style.marginLeft = width_px;
		this.current_width = this.width;
		pi_sensors_readings.update();
	},

	close: function()
	{
		document.getElementById("side_bar_panel").style.width = "0";
		document.getElementById("main_panel").style.marginLeft= "0";
		this.current_width = 0;
		pi_sensors_readings.update();
	},

	toggle:  function()
	{
		var width_px = this.width + "px";
		if (document.getElementById("side_bar_panel").style.width === width_px)
			this.close();
		else
			this.open();
	},
}

