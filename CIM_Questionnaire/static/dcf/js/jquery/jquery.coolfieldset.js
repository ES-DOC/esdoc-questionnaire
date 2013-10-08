/**
 * jQuery Plugin for creating collapsible fieldset
 * @requires jQuery 1.2 or later
 *
 * Copyright (c) 2010 Lucky <bogeyman2007@gmail.com>
 * Licensed under the GPL license:
 *   http://www.gnu.org/licenses/gpl.html
 *
 * "animation" and "speed" options are added by Mitch Kuppinger <dpneumo@gmail.com>
 */

(function($) {
	function hideFieldsetContent(obj, options){
		if(options.animation==true) {
                        /* MODIFIED BY AT */
                        // only hide the enclosing div of coolfielsets
                        // (not the help-button, nor all of the child divs)
			//obj.find('div').slideUp(options.speed);
                        //obj.find('div:not(.help-button)').slideUp(options.speed);
                        obj.find('div.coolfieldset-content').slideUp(options.speed);
                }
		else {
			//obj.find('div').hide();
                        //obj.find('div:not(.help-button)').hide();
                        obj.find('div.coolfieldset-content').hide();
                        /* END MODIFIED BY AT */
                }
		obj.removeClass("expanded");
		obj.addClass("collapsed");
	}
	
	function showFieldsetContent(obj, options){
		if(options.animation==true)
                        /* MODIFIED BY AT */
                        // see above
			obj.find('div.coolfieldset-content').slideDown(options.speed);
		else
			obj.find('div.coolfieldset-content').show();
                        /* END MODIFIED BY AT */
		obj.removeClass("collapsed");
		obj.addClass("expanded");
	}
	
	$.fn.coolfieldset = function(options){
		var setting={collapsed:false, animation:true, speed:'medium'};
		$.extend(setting, options);
		
		this.each(function(){
			var fieldset=$(this);
			var legend=fieldset.children('legend');
			
			if(setting.collapsed==true){
				legend.toggle(
					function(){
						showFieldsetContent(fieldset, setting);
					},
					function(){
						hideFieldsetContent(fieldset, setting);
					}
				)
				
				hideFieldsetContent(fieldset, {animation:false});
			}
			else{
				legend.toggle(
					function(){
						hideFieldsetContent(fieldset, setting);
					},
					function(){
						showFieldsetContent(fieldset, setting);
					}
				)
			}
		});
	}
})(jQuery);