/*glabal */! function($) {
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
			if(ajaxOptions.url === '/update' || ajaxOptions.url === '/inbox') {
				return;
			}
			$('#ajax-fail-modal').modal();
		});
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
					$('.comment-list-wrap').html('<ul>' + newComment + '</ul>');
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
		}; ! function() {
			poll(1, function() {
				poll();
			});
		}.delay(1000);
		//DOM ready后，延迟一秒再开始轮询comet服务器
		var notiTpl = '<li>{who}{op}{target}<span>{ctime}</span> <a rel="tooltip" data-uuid="{uuid}"  title="知道啦" href="javascript:;" class="iknow tip"><i class="icon-minus"></i></a></li>';
		$noteBtn.on('noticeclear', function(e, data) {
			$noteBtn.off('mouseenter', notiTipIn);
			$(document).on('click', notiTipOut);
			$('.notice-list').html('');
			$noteBtn.find('.bubble-dark').hide();
		}).on('noticearrival', function(e, data) {
			$noteBtn.on('mouseenter', notiTipIn);
			$(document).on('click', notiTipOut);
			var notices = data[0];
			var html = [];
			for(var i = 0; i < notices.length; i++) {
				html.push(notiTpl.assign({
					'who' : notices[i]['who'],
					'op' : notices[i]['op'],
					'target' : notices[i]['target'],
					'ctime' : Date.create(notices[i]['ctime']).format('{yyyy}-{MM}-{d} {hh}:{mm}:{ss}'),
					'uuid' : notices[i]['uuid'],
				}));
			}
			$('.notice-list').html(html.join(''));
			$noteBtn.find('.bubble-dark').text(data[1]).show();
			//TODO:闪烁信息数
			$('.bubble').text(data[1]);
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
		$('.notice-list').on('click', '.iknow', function() {
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
					$self.data('op', op.startsWith('un') ? op.from(2) : 'un' + op).siblings('span.count').text(data.data);
				} else {
					$('#global-ajax-indicator').trigger('ajaxError', [data.msg]);
				}
			});
		});
	});
}($);

/* message */
! function($) {
	var url = '/inbox';
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
					$self.siblings('.send-status').text('发送成功！'); ! function() {
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
! function($) {/**
	 * 上传图片
	 *
	 * @param {}
	 *            para_name 图片所属属性名
	 * @param {}
	 *            number 此类图片的总数量
	 */
	function submitImage(para_name, number) {
		var para_form = para_name + "_form";
		var para_image = para_name + "_image";
		// alert(para_image);
		for(var i = 1; i <= number; i++) {
			var srcValue = $("#" + para_image + i).attr("src");
			// alert(srcValue);
			// alert(srcValue.length);
			if(srcValue == "" || srcValue.length == 0) {
				// alert("break");
				break;
			}
		}
		if(i > number) {
			alert("已超过了此类图的上传最大限");
			// 重置上传按钮，使之为空
			resetUploadBotton(para_name + "_add");
		} else {
			$("#" + para_form).submit();
		}
	}

	/**
	 * iframe上传外观图片的返回操作
	 *
	 * @param {}
	 *            msg 返回的图片所在地址
	 */
	function callbackWaiguan(msg) {

		if(msg != "error") {
			for(var i = 1; i <= 3; i++) {
				var srcValue = $("#waiguan_image" + i).attr("src");
				// alert(srcValue);
				if(srcValue == "" || srcValue.length == 0) {
					$("#waiguan_image" + i).attr("src", msg);
					$("#waiguan_image" + i).css("visibility", "visible");
					$("#waiguan_delete_image" + i).css("visibility", "visible");
					$("#waiguan_delete_image" + i).click(function() {
						deleteImage("waiguan", i);
					});
					break;
				}
			}
		} else {
			alert("上传图片失败，后台程序出现问题！");
		}

		// 重置上传按钮，使之为空
		resetUploadBotton("waiguan_add");
	}
	$(function() {
		$('#avatar-file').on('change', function() {
			
		});
		$('#do-upload').click(function(){
			if()
		});
	});
}($);
