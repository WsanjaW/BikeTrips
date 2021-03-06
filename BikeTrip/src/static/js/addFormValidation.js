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
     		$.validator.addMethod('filesize', function(value, element, param) {
     		    // param = size (en bytes) 
     		    // element = element to validate (<input>)
     		    // value = value of the element (file name)
     		    return this.optional(element) || (element.files[0].size <= param) 
     		});
     		$('#addform').validate(
     	    		{
     	    			rules: {
     	    				trip_name: {
     	    					minlength: 2,
     	    					required: true
     	    				},
     	    				from_date: {
     	    					required: true,
     	    					date: true
     	    				},
     	    				to_date: {
     	    					required: true,
     	    					date: true
     	    				},
     	    				img: {
     	    				
     	    					filesize: 1048576,
     	    					accept: "image/*"
     	    					
     	    				},
     	    				cities: {
     	    					required: true,
     	    					cities: true
     	    				},
     	    				
     	    		    },
     	    		    messages: {
     	        			
     	        			trip_name: {
     	            			required: "Enter trip name",
     	            			minlength: jQuery.format("Enter at least {0} characters"),
     	            		},
     	            		img: {
     	            			filesize: "Image too large",
     	    					accept: "File must be image"
     	    					
     	    				},
     	    				cities: {
     	    					required: "Enter city",
     	    					cities: "Wrong format! format: First City, Secund City"
     	    				},
     	    				
     	            		
     	   				},
     	    			
     	   		 });
    }); // end document.ready