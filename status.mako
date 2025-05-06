<!DOCTYPE html>

<meta http-equiv="refresh" content="15">

<head>
<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/3.4.0/jquery.js"></script>
<script type="text/javascript" src="https://unpkg.com/tabulator-tables@4.2.5/dist/js/tabulator.min.js"></script>
<script type="text/javascript" src="https://momentjs.com/downloads/moment.js"></script>
<link href="https://unpkg.com/tabulator-tables@4.2.5/dist/css/tabulator.min.css" rel="stylesheet">
<script type="text/javascript">

function cellEdited(cell) {
  var d = cell.getRow().getData();
  $.ajax({
    url:"/status",
    method:"post",
    data: {c:"UBR", uuid:d.uuid, h:d.heartbeat, j:d.jitter}
  });
}


function onLoad() {

    var tabledata = [
    %for beacon in beacons:
    {
      ip:"${beacon.ip}",
    	uuid:"${beacon.mid}",
    	heartbeat:${beacon.heartbeat},
    	jitter:${beacon.jitter},
    	lci:"${beacon.lastCheckIn}",
    	nci:"${beacon.nextCheckIn}"
    },
    %endfor
    ];

    var table = new Tabulator("#beacontable", {
    	data:tabledata,
    	selectable:1,  //this says "only allow one row selected"
    	cellEdited:cellEdited,
    	ajaxType:"POST",
    	columns: [
          {title:"IP", field: "ip"},
    	    {title:"UUID", field:"uuid"},
    	    {title:"Heartbeat", field:"heartbeat", editor:"number"},
    	    {title:"Jitter", field:"jitter", editor:"number"},
    	    {title:"Last Check-in", field:"lci", formatter:"datetime",formatterParams:{outputFormat:"YYYY-MM-DD hh:mm:ss"}},
          {title:"Next Check-in", field:"nci", formatter:function(cell, formatterParams, onRendered){
              return moment(cell.getValue()).fromNow();
          }}
    	],
    });

    //Delete row on "Delete Row" button click
    $("#del-row").click(function(){
	   var table = this;
	   var selectedRows = table.getSelectedRows();
	   for (var i=0; i<selectedRows.length; i++){
	      row=selectedRows[i];
          var d = row.getData();
	      table.deleteRow(row);
          $.ajax({
             url:"/status",
             method:"post",
             data: {c:"DBR", uuid:d.uuid}
	         });
		  }
    }.bind(table));
}

</script>
</head>

<body onload="onLoad()">

<div class="table-controls">
      <button id="del-row">Delete selected row</button>
</div>

<div id="beacontable"></div>

</body>
</html>
