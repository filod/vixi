/*glabal */
!function($){
	
	
	
	//global close window
	$(function(){
		$('.alert').on('click','.close',function(e){
			$(e.delegateTarget).hide('slow');
			//TODO: set 'never see again' cookie
		});
		//bind global ajax event
		$('#global-ajax-indicator').on('ajaxSend',function(){
			$(this).show();
		}).on('ajaxComplete',function(){
			$(this).hide();
		}).on('ajaxError',function(e,jqXHR,data){
			$('#ajax-fail-modal').modal();
		});
	});
}($);


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
		$notePanel = $('#global-notifacation');
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
		$(document).on('click',function(){
			$('.popover').removeClass('in fade');
		});
	});
}($);

/*follow opration*/
!function($){
	var url = '/follow'
	$(function(){
		$('#do-follow').click(function(){
			$self = $(this);
			$.post(url,{'target':$(this).data('target'),
						'op' : $(this).data('op'),
						'toid' : $(this).data('toid')
			}).success(function(data){
				if(data && data.res_stat == 'success'){
					$self.data('op',$self.data('op').trim() === 'unfollow'? 'follow' : 'unfollow' ).toggleClass('btn-success');
					$self.html($self.text().trim() === "关注" ? "取消关注" : "<i class='icon-heart icon-white'></i>关注 ");
				}else{
					$('#global-ajax-indicator').trigger('ajaxError',[ data.msg ])
				}
			});
		})
	})
}($);

/*comment opration*/
!function($){
	var url = '/comment/add';
	var comment_tpl = '<li> \
		<div class="comment-entry-wrap"> \
			<div class="entry-meta"> \
				<img width="30" src="{avatar}" alt="{name}" /> \
				<a  class="author" href="/people/{{uid}}">{name}</a> \
				<span class="time">{now}</span> \
			</div> \
			<div class="entry-content"> \
				<p> \
					{content} \
				</p> \
			</div> \
			<div class="entry-util"> \
				<a class="reply" href="javascript:;">回复</a> \
			</div> \
		</div> \
	</li>';
	$(function(){
		$('.comment-wrap').on('click','.do-comment',function(e){
			$self = $(this);
			$.post(url,{'content':$(e.delegateTarget).find('textarea').val(),
						'wid' : $(this).data('wid')						
			}).success(function(data){  
				$('.comment-list-wrap ul').append(comment_tpl.assign({
					'name'  : vixi.current_user.name,
					'uid' : vixi.current_user.uid,
					'avatar' : vixi.current_user.avatar,
					'now' : new Date().format('{yyyy}-{MM}-{d} {hh}:{mm}:{ss}'),
					'content' : $(e.delegateTarget).find('textarea').val()
				}));
				$(e.delegateTarget).find('textarea').val('')
			});
		}).on('click','.close-comment',function(e){
			$(e.delegateTarget).slideUp('fast')
		})
	})
}($);
/*comments loading*/
!function($){
	var url = '/comment/list';
	var tpl = '';
	$(function(){
		$clw = $('.comment-list-wrap');
		$clw.text('正在加载评论...').load(url+"?wid="+$clw.data('wid'),function(){
		}).on('click','.reply',function(e){
			$('.comment-wrap').find('textarea').trigger('focus').val('回复：'+$(this).parent().siblings('.entry-meta').find('.author').text());
		});
	})
}($);




