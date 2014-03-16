		
   		$(document).ready(function(){
   		// override jquery validate plugin defaults
			$.validator.setDefaults({
			    highlight: function(element) {
			        $(element).closest('.form-group').addClass('has-error');
			    },
			    unhighlight: function(element) {
			        $(element).closest('.form-group').removeClass('has-error');
			    },
			    errorElement: 'span',
			    errorClass: 'help-block',
			    errorPlacement: function(error, element) {
			        if(element.parent('.input-group').length) {
			            error.insertAfter(element.parent());
			        } else {
			            error.insertAfter(element);
			        }
			    }
			});
   			jQuery.validator.addMethod("gpx", function(value, element) {
   				if(value.indexOf(".gpx") > -1){
   					return true;
   				}
   				return false;
     			
			}, "false");
   			jQuery.validator.addMethod("cities", function(value, element) {
     			if (value.search(/[!@#$%^&\*\(\)_\+\?><\.\/\\|]/)  > -1){
     				return false;
     			}
     			if (value.search(/[0-9]/)  > -1){
     				return false;
     			}
     			if (value.search(/([a-zA-Z ],)*[a-zA-Z ]/)  > -1){
     				return true;
     			}
				return false;
			}, "false");
    		$('#addtrackform').validate(
    		{
    			rules: {
    				trip_name: {
    					minlength: 2,
    					required: true
    				},
    				file: {
    					required: true,
    					gpx: true
    					
    					
    				},
    				
    				
    		    },
    		    messages: {
        			
        			trip_name: {
            			required: "Enter trip name",
            			minlength: jQuery.format("Enter at least {0} characters"),
            		},
            		file: {
    				
    					gpx: "File must be .gpx",
    				
    					
    				},    				
            		
   				},

   		 	});
    		
    }); // end document.ready