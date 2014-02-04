		
   		$(document).ready(function(){
   			
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
    		$('#fif').validate(
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
    			highlight: function(element) {
    				$(element).closest('.control-group').removeClass('success').addClass('error');
    			},
    			success: function(element) {
    				element
    					.text('OK!').addClass('valid')
    						.closest('.control-group').removeClass('error').addClass('success');
    			}
   		 	});
    		$('#uf').validate(
    	    		{
    	    			rules: {
    	    				change_trip_name: {
    	    					minlength: 2,
    	    					required: true
    	    				},
    	    				
    	    		    },
    	    		    messages: {
    	        			
    	    		    	change_trip_name: {
    	            			required: "Enter trip name",
    	            			minlength: jQuery.format("Enter at least {0} characters"),
    	            		},

    	   				},
    	    			highlight: function(element) {
    	    				$(element).closest('.control-group').removeClass('success').addClass('error');
    	    			},
    	    			success: function(element) {
    	    				element
    	    					.text('OK!').addClass('valid')
    	    						.closest('.control-group').removeClass('error').addClass('success');
    	    			},
                        //perform an AJAX call 
                        submitHandler: function() {
                            // Grabs the text input trip_id
                            var name = $("#uname").val();
                            var trip_id = $("#trip_id").val();
                    		var form_id = 'nuf';
                            var dataString = 'txtValue='+ name + '&' + 'trip_id=' + trip_id + '&form_id=' +form_id;   

                            // This creates the AJAX connection
                            $.ajax({
                                type: "POST",
                                url: "/update",
                                data: dataString,
                                success: function(data) {
                                    $('#trip_name').html(data.text);
                                    $('[name="updatediv"]').hide();
                                    open1 = 1;
                                    
                                }
                            });
                        }
    	   		 });
    		$('#un').validate(
    	    		{
    	    			rules: {
    	    				change_cities: {
    	    					required: true,
    	    					cities: true
    	    				},
    	    				
    	    		    },
    	    		    messages: {
    	        			
    	    		    	change_cities: {
    	    		    		required: "Enter city",
     	    					cities: "Wrong format! format: First City, Secund City"
    	            		},

    	   				},
    	    			highlight: function(element) {
    	    				$(element).closest('.control-group').removeClass('success').addClass('error');
    	    			},
    	    			success: function(element) {
    	    				element
    	    					.text('OK!').addClass('valid')
    	    						.closest('.control-group').removeClass('error').addClass('success');
    	    			},
                        //perform an AJAX call 
                        submitHandler: function() {
                        	
                        	var cities = $("#ucities").val();
                        	var trip_id = $("#trip_id").val();
                    		var form_id = 'cuf';
                            var dataString = 'txtValue='+ cities + '&' + 'trip_id=' + trip_id + '&form_id=' +form_id;   

                            // This creates the AJAX connection
                            $.ajax({
                                type: "POST",
                                url: "/update",
                                data: dataString,
                                success: function(data) {
                                	var list = data.text.split(",");
                                	var txt = "Cities:" 
                                	for (var x in list)
          							{
          								txt=txt + "<a href='/cityinfo?city="+ list[x] + "'"+ "id='cities' >"+list[x] +",</a>" ;
          							}
                                    $('#cities').html(txt);
                                    $('[name="updatediv"]').hide();
                                    open1 = 1;
                                    
                                }
                            });
                        }
    	   		 });
    }); // end document.ready