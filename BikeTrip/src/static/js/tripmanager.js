function createTree(tree) {
	var setting = {
			data: {
				simpleData: {
						enable: true
				}
			}
		};

	var zNodes = tree;

	$(document).ready(function(){
		$.fn.zTree.init($("#treeDemo"), setting, zNodes);
	});
}

function crateTags(location,type,season) {
	
	$(function() {
        // If using Bootstrap 2, be sure to include:
        // Tags.bootstrapVersion = "2";
        var l=$('#location-tag-list').tags({
			tagSize: "md",
			tagClass:"btn-warning",
			suggestions: location,
            afterAddingTag: function(tag){
            	var lelem = document.getElementById("locationfilter");
            	lelem.value = "";
				lelem.value += l.getTags();
			},
            afterDeletingTag: function(tag){
            	var lelem = document.getElementById("locationfilter");
            	lelem.value = "";
				lelem.value += l.getTags();
			}
           
        });
		var t = $('#type-tag-list').tags({
			tagSize: "md",
			suggestions: type,
            afterAddingTag: function(tag){
            	var lelem = document.getElementById("typefilter");
            	lelem.value = "";
				lelem.value += t.getTags();
			},
			afterDeletingTag: function(tag){
            	var lelem = document.getElementById("typefilter");
            	lelem.value = "";
				lelem.value += t.getTags();
			}
        });
		var s = $('#season-tag-list').tags({
			tagSize: "md",
			suggestions: season,
            afterAddingTag: function(tag){
            	var lelem = document.getElementById("seasonfilter");
            	lelem.value = "";
				lelem.value += s.getTags();
			},
			afterDeletingTag: function(tag){
            	var lelem = document.getElementById("seasonfilter");
            	lelem.value = "";
				lelem.value += s.getTags();
			}
        });
    });

}
var loc;
var typ;
var ses;
function crateAddTags(location,type,season) {
	
	$(function() {
        // If using Bootstrap 2, be sure to include:
        // Tags.bootstrapVersion = "2";
        loc=$('#location-tag-list-add').tags({
			tagSize: "md",
			tagClass:"btn-warning",
			suggestions: location,
            afterAddingTag: function(tag){
            	var lelem = document.getElementById("location");
            	lelem.value = "";
				lelem.value += loc.getTags();
			},
            afterDeletingTag: function(tag){
            	var lelem = document.getElementById("location");
            	lelem.value = "";
				lelem.value += loc.getTags();
			}
           
        });
		typ = $('#type-tag-list-add').tags({
			tagSize: "md",
			suggestions: type,
            afterAddingTag: function(tag){
            	var lelem = document.getElementById("type");
            	lelem.value = "";
				lelem.value += typ.getTags();
			},
			afterDeletingTag: function(tag){
            	var lelem = document.getElementById("type");
            	lelem.value = "";
				lelem.value += typ.getTags();
			}
        });
		ses = $('#season-tag-list-add').tags({
			tagSize: "md",
			suggestions: season,
            afterAddingTag: function(tag){
            	var lelem = document.getElementById("season");
            	lelem.value = "";
				lelem.value += ses.getTags();
			},
			afterDeletingTag: function(tag){
            	var lelem = document.getElementById("season");
            	lelem.value = "";
				lelem.value += ses.getTags();
			}
        });
    });

}
function addLocTag(value){
	
	$('#location-tag-list').tags().addTag(value);
}
function addTypeTag(value){
	
	$('#type-tag-list').tags().addTag(value);
}
function addSeasonTag(value){
	
	$('#season-tag-list').tags().addTag(value);
}
function crateUpdateTags(location,type,season,add_location,add_type,add_season) {
	
	$(function() {
        // If using Bootstrap 2, be sure to include:
        // Tags.bootstrapVersion = "2";
        var loc=$('#location-tag-list-add').tags({
			tagSize: "md",
			tagClass:"btn-warning",
			tagData: add_location,
			suggestions: location,
            afterAddingTag: function(tag){
            	var lelem = document.getElementById("location");
            	lelem.value = "";
				lelem.value += loc.getTags();
			},
            afterDeletingTag: function(tag){
            	var lelem = document.getElementById("location");
            	lelem.value = "";
				lelem.value += loc.getTags();
			}
           
        });
		var typ = $('#type-tag-list-add').tags({
			tagSize: "md",
			tagData: add_type,
			suggestions: type,
            afterAddingTag: function(tag){
            	var lelem = document.getElementById("type");
            	lelem.value = "";
				lelem.value += typ.getTags();
			},
			afterDeletingTag: function(tag){
            	var lelem = document.getElementById("type");
            	lelem.value = "";
				lelem.value += typ.getTags();
			}
        });
		var ses = $('#season-tag-list-add').tags({
			tagSize: "md",
			tagData: add_season,
			suggestions: season,
            afterAddingTag: function(tag){
            	var lelem = document.getElementById("season");
            	lelem.value = "";
				lelem.value += ses.getTags();
			},
			afterDeletingTag: function(tag){
            	var lelem = document.getElementById("season");
            	lelem.value = "";
				lelem.value += ses.getTags();
			}
        });
    });

}