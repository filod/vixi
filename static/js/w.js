util = (function($){
	var util = {};
	/**
	 * 
	 */
	util.toast = function(msg){
		$('body').append($('<div class="toast alert alert-success">{1}</div>'.assign(msg)));
		~function(){
			$('.toast').fadeOut('fast');
		}.delay(1000);
		
	}
	return util;
})($);
/*glabal */
! function($) {
	//global close window
	$(function() {
		$('.alert').on('click', '.close', function(e) {
			$(e.delegateTarget).hide('slow');
			//TODO: set 'never see again' cookie
		});
		// $('.notice-list').on('mouseout','.tip',function(){
		// $(this).tooltip('show');
		// }).on('mouseout','.tip',function(){
		// $(this).tooltip('hide');
		// });
		//bind global ajax event
		$('#global-ajax-indicator').on('ajaxSend', function(e, jqxhr, ajaxOptions) {
			if(ajaxOptions.url === '/update') {
				return;
			}
			$(this).show();
		}).on('ajaxComplete', function() {
			$(this).hide();
		}).on('ajaxError', function(e, jqXHR, ajaxOptions) {
			if(ajaxOptions.url === '/update' || ajaxOptions.url.startsWith('/inbox')) {
				return;
			}
			$('#ajax-fail-modal').modal();
		});
		//tab hash 追踪
		$('body').on('click.tab.data-api', '[data-toggle="tab"], [data-toggle="pill"]',function(e){
			document.location.hash = 'tab_'+$(e.target).attr('href').split('#')[1];
		});
		//激活tab
		if(document.location.hash){
			var selector = document.location.hash.replace('tab_','');
			$('[href="'+selector+'"]').trigger('click.tab.data-api');
		}
		//tooltip
		$('[rel="tooltip"]').tooltip();
	});
}($);

/*global-header:*/
! function($) {
	$(function() {
	});
}($);

/*follow */
! function($) {
	var url = '/follow';
	$(function() {
		$('#do-follow').click(function() {
			$self = $(this);
			$.post(url, {
				'target' : $(this).data('target'),
				'op' : $(this).data('op'),
				'toid' : $(this).data('toid')
			}).success(function(data) {
				if(data && data.res_stat === 'success' && data.ret == '002') {
					$self.data('op', $self.data('op').trim() === 'unfollow' ? 'follow' : 'unfollow').toggleClass('btn-success');
					$self.html($self.text().trim() === "关注" ? "取消关注" : "<i class='icon-heart icon-white'></i>关注 ");
				} else {
					$('#global-ajax-indicator').trigger('ajaxError', [data.msg]);
				}
			});
		});
	});
}($);

/* comment */
! function($) {
	var url = '/comment/add';
	var comment_tpl = '<li><div class="comment-entry-wrap"><div class="entry-meta"><img width="30" src="{avatar}" alt="{name}" /><a  class="author" href="/people/{{uid}}">{name}</a> <span class="time">{now}</span> </div> <div class="entry-content"> <p>{content} </p> </div> <div class="entry-util"></div></div></li>';
	$(function() {
		$('.comment-wrap').on('click', '.do-comment', function(e) {
			var $self = $(this);
			var $txt_comment = $(e.delegateTarget).find('textarea');
			$.post(url, {
				'content' : $txt_comment.val(),
				'wid' : $(this).data('wid'),
				'reply_uid' : $('#reply_uid').val(),
				'reply_cid' : $('#reply_cid').val(),
			}).success(function(data) {
				var newComment = comment_tpl.assign({
					'name' : vixi.current_user.name,
					'uid' : vixi.current_user.uid,
					'avatar' : vixi.current_user.avatar,
					'now' : new Date().format('{yyyy}-{MM}-{d} {hh}:{mm}:{ss}'),
					'content' : $txt_comment.val().escapeHTML()
				});
				$clw = $('.comment-list-wrap');
				if($clw.find('ul').length === 0) {
					$('.comment-list-wrap').html('<ul class="entry-list comment-list">' + newComment + '</ul>');
				} else {
					$clw.find('ul').append(newComment);
				}
				$txt_comment.val('');
			});
		}).on('click', '.close-comment', function(e) {
			$(e.delegateTarget).slideUp('fast');
		}).find('textarea').keyup(function(e) {
			if($(this).val() === '') {
				$('#reply_uid').val('');
				$('#reply_cid').val('');
			}
		});
	});
	var listUrl = '/comment/list';
	$(function() {
		$clw = $('.comment-list-wrap');
		$clw.text('正在加载评论...').load(listUrl + "?wid=" + $clw.data('wid'), function() {
		}).on('click', '.reply', function(e) {
			$('#reply_uid').val($(this).data('uid'));
			$('#reply_cid').val($(this).data('cid'));
			$('.comment-wrap').find('textarea').trigger('focus').val('回复 ' + $(this).parent().siblings('.entry-meta').find('.author').text() + '：');
		});
	});
}($);
/* notice */
! function($) {
	var url = '/update';
	$(function() {
		$noteBtn = $('#global-notifacation');
		var notiTipIn = function() {
			$('#notifacation-panel').fadeIn().addClass('bottom');
		};
		var notiTipOut = function() {
			$('#notifacation-panel').hide();
		};
		var poll = function(atonce, callback) {
			$.post(url, {
				'atonce' : atonce
			}).success(function(data) {
				if(data && data.data && data.data[1] > 0) {
					$noteBtn.trigger('noticearrival', [data.data]);
					$('.clear-notice').trigger('noticearrival');
				} else if(data && data.data && data.data[1] === 0) {
					$noteBtn.trigger('noticeclear', [data.data]);
					$('.clear-notice').trigger('noticeclear');
				}
				if(atonce) {
					//如果atonce请求，则只发出一次请求
				} else {//否则轮询
					setTimeout(poll, 0);
				}
				if($.isFunction(callback)) {
					callback();
				}
			});
		};
		! function() {
			poll(1, function() {
				poll();
			});
		}.delay(1000);
		//DOM ready后，延迟一秒再开始轮询comet服务器
		var notiTpl = '<li>{who}{op}{target}<span class="time">{ctime}</span> <a rel="tooltip" data-uuid="{uuid}"  title="知道啦" href="javascript:;" class="iknow tip"><i class="icon-minus"></i></a></li>';
		$noteBtn.on('noticeclear', function(e, data) {
			$noteBtn.off('mouseenter', notiTipIn);
			$(document).on('click', notiTipOut);
			$('.notice-list').html('');
			$noteBtn.find('.bubble-dark').hide();
		}).on('noticearrival', function(e, data) {
			$noteBtn.on('mouseenter', notiTipIn);
			$(document).on('click', notiTipOut);
			$("#global-header").on('click', notiTipOut);
			var notices = data[0];
			var html = [];
			for(var i = 0; i < notices.length; i++) {
				html.push(notiTpl.assign({
					'who' : notices[i]['who'],
					'op' : notices[i]['op'],
					'target' : notices[i]['target'],
					'ctime' : Date.create(notices[i]['ctime']).format('{yyyy}-{MM}-{dd} {hh}:{mm}'),
					'uuid' : notices[i]['uuid'],
				}));
			}
			$('.notice-list').html(html.join(''));
			// $noteBtn.find('').text(data[1]).show();
			$('.bubble-dark,.bubble-light').text(data[1]).show();
			//TODO:闪烁信息数
			$('.bubble').text();
			document.title = document.title.replace(/\(\d+\)\s+/g,'');
			document.title ='({1}) '.assign(data[1]) + document.title;
		});
		var clearurl = '/notice/clear';
		$('.clear-notice').click(function() {
			$self = $(this);
			$.post(clearurl).success(function(data) {
				if(data.ret === '202') {
					$self.trigger('noticeclear');
					$noteBtn.trigger('noticeclear');
				}
			});
		}).on('noticeclear', function(e, data) {
			$('.clear-notice').addClass('disabled').prop('disabled', true);
			$('.notice-list').html('没有未读通知，你可以查看全部通知');
			$('.bubble').text('0');
			return false;
		}).on('noticearrival', function(e, data) {
			$(this).removeClass('disabled').prop('disabled', false);
			
			return false;
		});
		$('.notice-list,.unread-list').on('click', '.iknow', function() {
			$self = $(this);
			$.post('/notice/mark', {
				'noti_uuid' : $self.data('uuid')
			}, function(data) {
				if(data.ret === '203') {
					$self.parent().fadeOut('slow');
					poll(1);
				}
			});
		});
	});
}($);

/* "more" things */
!function($){
	var more_handler = {
		home_feed : function (e){
			var url = document.location.pathname;
			return more_handler.feed.call(this,e,url);
		},
		people_feed : function(e){
			var url = document.location.pathname+ "/more/feed";
			return more_handler.feed.call(this,e,url);
		},
		feed : function(e,url){
			var $self = $(this);
			return $.post(url,{'before' : $('.timeline-list li:last-child .feed-ctime').val()}).success(function(data){
				if(data && data.data && data.data.count > 0) {
					$('.timeline-list').append(data.data.html);
				}
			});
		},
		unread : function(e){
			var url = '/notice/more/unread';
			return more_handler.noti.call(this,e,url,$('.unread-list'));
		},
		allnoti : function(e){ 
			var url = '/notice/more/all';
			return more_handler.noti.call(this,e,url,$('.allnoti-list'));
		},
		noti : function(e,url,$list){
			var $self = $(this);
			return $.post(url,{'nextpage':$self.data('nextpage')}).success(function(data){
				if(data && data.data.notice){
					$list.append(data.data.notice);	
				}
			});
		},
		atme : function(e){
			var url = '/wish/list/more/atme';
			return more_handler.wish.call(this,e,url,$('atme-list'));
		},
		iwish : function(e){
			var url = '/wish/list/more/iwish';
			return more_handler.wish.call(this,e,url,$('iwish-list'));		
		},
		ifollow_wish : function(e){
			var url = '/wish/list/more/ifollow';			
			return more_handler.wish.call(this,e,url,$('ifollow-list'));
		},
		public_wish : function(e){
			var url = document.location.pathname+'/more/public';
			return more_handler.wish.call(this,e,url,$('public-list'));
		},
		wish : function(e,url,$list){
			var $self = $(this);
			return $.post(url,{'nextpage':$self.data('nextpage')}).success(function(data){
				if(data && data.data.html){
					$list.append(data.data.html);	
				}		
			});
		},
		conversation : function(e,url){
			var url = url || document.location.pathname;
			var $self = $(this);
			return $.post(url,{'nextpage':$self.data('nextpage')}).success(function(data){
				if(data && data.data.html){
					$('.message-list').append(data.data.html);	
				}			
			});
		},
		conversation_list : function(e){
			return more_handler.wish.call(this,e,'/inbox/more/conversation');
		}
	}
	$(function(){
		$('.btn-more').click(function(e){
			var $self = $(this);
			more_handler[$(this).data('type').replace('-','_')].call(this,e).success(function(data){
				if(data && data.data && data.data.count > 0){
					$self.data('nextpage',data.data.nextpage);
					$self.trigger('loaded');
				}else if(data && data.data && data.data.count === 0) {
					$self.trigger('nomore');
				}else{
					$self.trigger('ajaxError');
				}
			}).fail(function(data){
				$self.trigger('loaded');
			});
			$self.trigger('loading');
		}).on('nomore',function(){
			//TODO 关注更多人&愿望的引导
			$(this).text('没有更多了~').prop('disabled',true);
		}).on('loading',function(){
			//TODO 添加加载动画
			$(this).text('加载中...').prop('disabled',true);
		}).on('loaded',function(){
			$(this).text('更多...').prop('disabled',false);
		});
	});
}($);

/* vote */
! function($) {
	$(function() {
		var url = '/vote';
		$('button.bless,button.curse').on('click', function() {
			$self = $(this);
			if($self.data('op') === 'curse' && vixi.current_user.uid.toNumber() === $self.parents('.wish-entry-wrap').data('uid')) {
				alert('搞错没……自己诅咒自己……不过，未息允许这样疯狂的行为……');
			}
			$.post(url, {
				'op' : $(this).data('op'),
				'toid' : $(this).data('toid')
			}).success(function(data) {
				if(data && data.res_stat === 'success') {
					var op = $self.data('op').trim();
					if($self.hasClass('bless')) {
						$self.text($self.text().trim().startsWith("祝福") ? "已祝福" : "").prop('disabled', true).removeClass('btn-danger');
					}
					if($self.hasClass('curse')) {
						$self.text($self.text().trim().startsWith("诅咒") ? "取消诅咒" : "诅咒Ta… ");
					}
					$self.data('op', op.startsWith('un') ? op.from(2) : 'un' + op).siblings('span.vote-count').text(data.data);
				} else {
					$('#global-ajax-indicator').trigger('ajaxError', [data.msg]);
				}
			});
		});
	});
}($);

/* message */
! function($) {
	var url = '/inbox/send';
	$(function() {
		$('.send-message').click(function(e) {
			$('#msg-modal').modal();
		});
		$('#do-send-message').click(function(e) {
			$self = $(this);
			$self.siblings('.send-status').text('发送中…');
			$.post(url, {
				'content' : $('#msg-content').val(),
				'to_uid' : $self.data('uid')
			}).done(function(data) {
				if(data && data.ret === '300') {
					if(document.location.pathname.startsWith('/inbox')){
						document.location.reload();
						return
					}
					$self.siblings('.send-status').text('发送成功！');
					! function() {
						$('#msg-modal').modal('hide');
						$self.siblings('.send-status').text('');
					}.delay(600);
				}
			}).fail(function() {
				$self.siblings('.send-status').addClass('error').text('发送失败!');
			});
		});
	});
}($);

/*upload*/
! function($) {
	$(function() {
		$('#do-upload').click(function() {
			callbackname = 'vixi' + $.now();
			window[callbackname] = function(data) {
				if(data.ret === 'success') {
					$('.avatar-preview').attr('src', data.url);
					$('#avatar-input').val(data.url);
					//TODO: reset form
				}
			}
			$('#callback-input').val(callbackname);
		});
	});
}($);

/*settings*/
! function($) {
	$(function() {
		function get_form_map($form) {
			var map = {}
			$form.find('input,textarea').not('[type="submit"]').each(function(idx, el) {
				var $el = $(el);
				if($el.is(':radio') || $el.is(':checkbox')){
					if($el.is(':checked')){
						map[$el.attr('name')] = $el.val();
					}else{
						map[$el.attr('name')] = '';
					}
				}else{
					map[$el.attr('name')] = $el.val();
				}
			});
			return map;
		}


		$('.ajax-form').submit(function() {
			var url = $(this).attr('action');
			var $self = $(this)
			$.post(url, get_form_map($self)).success(function(data) {
				util.toast(data.msg);
			});
			return false;
		});
		if(vixi.current_user['settings']) {
			for(key in vixi.current_user['settings']) {
				var $tar = $('input[name="' + key + '"]');
				if($tar.is(':radio')) {
					$tar.each(function(idx, el) {
						if($(el).val() === vixi.current_user['settings'][key]) {
							$(el).prop('checked', true);
						}
					});
				}
			}
		}
	});
}($);

/* wish realize*/
!function($){
	$(function(){
		$('.realize').click(function(){
			$('#realize-modal').modal();
		});
		$('#do-realize').click(function(e){
			var $self = $(this);
			var url = document.location.pathname + '/realize';  
			$.post(url,{'mdata':$('#mdata-content').val()}).success(function(data){
				$('#realize-modal').modal('hide');
				util.toast(data.msg);
				if(data.ret === '002'){
					$('.realize').prop('disabled',true).text('已实现');//.find('i').remove()				
				}
			});
		});
	});
}($);

//pending
!function($){
	$(function(){
		
	});
}($);

