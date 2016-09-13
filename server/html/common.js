//	Copyright 2016 Paul Broadhead
//	Contact: pjbroad@twinmoons.org.uk
//
//	This program is free software: you can redistribute it and/or modify
//	it under the terms of the GNU General Public License as published by
//	the Free Software Foundation, either version 3 of the License, or
//	(at your option) any later version.
//
//	This program is distributed in the hope that it will be useful,
//	but WITHOUT ANY WARRANTY; without even the implied warranty of
//	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//	GNU General Public License for more details.
//
//	You should have received a copy of the GNU General Public License
//	along with this program.  If not, see <http://www.gnu.org/licenses/>.

"use strict";

var request_common = request_common ||
{
	get_post_callback: function(handler)
	{
		if (this.readyState === this.DONE)
		{
			if (this.status === 200)
			{
				if (!this.responseText || this.responseText.length === 0)
				{
					error_message.display("Empty response for get_data()");
					return;
				}
				var response = JSON.parse(this.responseText);
				if (typeof response.status === "undefined")
					error_message.display("Invalid response for getdata: " + this.responseText);
				else if (!response.status)
				{
					if ((typeof response.message === "undefined") || (response.message.length<=0))
						error_message.display("Unknown error");
					else
						error_message.display(response.message);
				}
				else
					handler(response);
			}
			else
				error_message.display("Unexpected http status code: " + this.status);
		}
	},

	get_data: function(url, handler)
	{
		var request = new XMLHttpRequest();
		request.onreadystatechange = function() { request_common.get_post_callback.bind(this)(handler); };
		request.open("GET", url);
		try
		{
			request.send();
		}
		catch (err)
		{
			error_message.display("Failed to get data: " + err.message);
		}
	},

	post_data: function(url, handler, data)
	{
		var request = new XMLHttpRequest();
		request.onreadystatechange = function() { request_common.get_post_callback.bind(this)(handler); };
		request.open("POST", url);
		try
		{
			request.send(JSON.stringify(data));
		}
		catch (err)
		{
			error_message.display("Failed to get data: " + err.message);
		}
	}

}


var integer_date = integer_date ||
{

	date2yyyymmdd: function(thedate)
	{
		return thedate.getFullYear() * 10000 + (thedate.getMonth() + 1) * 100 + thedate.getDate();
	},

	yyyymmdd2date: function(thedate, hours, minutes, seconds)
	{
		hours = (typeof hours === 'undefined') ? 12 : hours;
		minutes = (typeof minutes === 'undefined') ? 0 : minutes;
		seconds = (typeof seconds === 'undefined') ? 0 : seconds;
		var datenum = parseInt(thedate,10);
		if (isNaN(datenum) || !isFinite(datenum))
			return "";
		var year = parseInt(datenum / 10000, 10);
		var month = parseInt((datenum / 100) % 100, 10) - 1;
		var day = parseInt(datenum % 100, 10);
		var nd = new Date(year, month, day, hours, minutes, seconds, 0);
		return nd;
	}
}


var error_message = error_message ||
{
	display: function(message)
	{
		var panel_h = document.getElementById("error_message_panel");
		if (message && message.length > 0)
			panel_h.innerHTML = message;
		else
			panel_h.innerHTML = "";
	},

	clear: function()
	{
		this.display(null);
	}
}
