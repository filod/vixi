/*global-header:*/
!function($){
	var delayid ;
	var notetpl = '<div class="notifacation-panel"> \
								   <div class="">\
									   <p></p>\
									   <ul class="notifacation-list"></ul>\
										   <a href="" class="btn">我知道啦</a>\
										   <a href="" class="btn btn-primary">查看全部</a>\
								   </div>\
						   </div>';
	var note = notetpl;
	$(function(){
		$notePanel = $('.pop-tip');
		$notePanel.StayPopover({
			animation : true,
			placement:'bottom',
			title : '通知',
			trigger : 'hover',
			content: note,
	 		delay:{
	 			show : 100,
	 			hide : 1000
	 		}
	 	});
	})
}($);


