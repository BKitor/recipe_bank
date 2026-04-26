/*
 * jQuery throttle / debounce - v1.1 - 3/7/2010
 * http://benalman.com/projects/jquery-throttle-debounce-plugin/
 * 
 * Copyright (c) 2010 "Cowboy" Ben Alman
 * Dual licensed under the MIT and GPL licenses.
 * http://benalman.com/about/license/
 */
(function(b,c){var $=b.jQuery||b.Cowboy||(b.Cowboy={}),a;$.throttle=a=function(e,f,j,i){var h,d=0;if(typeof f!=="boolean"){i=j;j=f;f=c}function g(){var o=this,m=+new Date()-d,n=arguments;function l(){d=+new Date();j.apply(o,n)}function k(){h=c}if(i&&!h){l()}h&&clearTimeout(h);if(i===c&&m>e){l()}else{if(f!==true){h=setTimeout(i?k:l,i===c?e-m:e)}}}if($.guid){g.guid=j.guid=j.guid||$.guid++}return g};$.debounce=function(d,e,f){return f===c?a(d,e,false):a(d,f,e!==false)}})(this);

jQuery(document).ready(function() {
	if (typeof(ABalytics)!=="undefined") {
		ABalytics.applyHtml();
	}
	
	var $body = jQuery('body');
	var $window = jQuery(window);	
	var $menu = jQuery('#menu');
	var $togglemenu = jQuery('#mobtoggles');

	var dropdownToggle = jQuery('<button/>',{
		'class':'dropdown-toggle'
	}).append(jQuery('<span/>',{
		'class':'screen-reader-text',
		text:'Toggle submenu'
	}));

	$menu.find('li.menu-item-has-children').append(dropdownToggle);
	$menu.find('li.menu-item-has-children.current-menu-item>.submenu, li.menu-item-has-children.current-menu-ancestor>.submenu').attr('style','display:block').parent().addClass('open');

	$menu.on('click','.dropdown-toggle',function(e) {
		var $li = jQuery(this).closest('li');
		var $submenu = $li.children('.submenu');

		if ($li.hasClass('open')) {
			$li.removeClass('open');
			$submenu.stop().slideUp(300,function() {
				jQuery(this).css('height','');
			});
		} else {
			$li.addClass('open');
			$submenu.stop().slideDown(300,function() {
				jQuery(this).css('height','');
			});
		}
	});

	function handleDropdowns() {
		var pos = jQuery(this).offset().left + jQuery(this).children('.submenu').width() + 20;
		var available = $window.width();
		jQuery(this).children('.submenu').css({left:Math.min(0,available-pos)});
	}

	var applydropdown = false;
	$window.on('resize orientationchange',jQuery.throttle(100,function() {
		var shouldapplydropdown = !$togglemenu.is(':visible');
		if (applydropdown!=shouldapplydropdown) {
			applydropdown = shouldapplydropdown;
			if (applydropdown) {
				$menu.on('mouseenter','ul.menu>li.menu-item-has-children',handleDropdowns);
			} else {
				$menu.off('mouseenter','ul.menu>li.menu-item-has-children',handleDropdowns);
			}
		}
	})).triggerHandler('resize');

	jQuery('#menu').find('ul.menu').menuAim({
		activate:function(row) {
			jQuery(row).addClass('active');

		},
		deactivate:function(row) {
			jQuery(row).removeClass('active');
		},
		exitMenu:function() {
			return true;
		},
		tolerance: 0,
		submenuDivSelector:".submenu",
		submenuSelector:".menu-item-has-children"
	});	
	
	jQuery('article.postdiv.withoverlays .content').find('.aligncenter, .alignleft, .alignright, .alignnone').first().each(function() {
		$img = jQuery(this);

		var type = '';

		if ($img.is('.wp-caption')) {
			$img = $img.find('img');
			type = 'withcaption';
		} else if ($img.hasClass('aligncenter')) {
			type = 'aligncenter';
		} else if ($img.hasClass('alignleft')) {
			type = 'alignleft';
		} else if ($img.hasClass('alignright')) {
			type = 'alignright';
		} else if ($img.hasClass('alignnone')) {
			type = 'alignnone';
		}
		$img.removeClass('alignnone aligncenter alignleft alignright').wrap('<span class="firstimage '+type+'"><span class="firstimage-a"></span></span>').parent().append(jQuery(this).closest('article.postdiv').find('.post-header .overlays'));
	});
	
	jQuery('.togglesearch, .closesearch').click(function(e) {
		e.preventDefault();
		$body.toggleClass('searchopen');
		
		if ($body.hasClass('searchopen')) {
			setTimeout(function() {
				jQuery('#searchbar').find('.searchform input[type="text"]').focus();
			},500);		
		}		
	});
	jQuery('.togglemenu, .closemenu, #menuoverlay').click(function(e) {
		e.preventDefault();
		$body.toggleClass('menuopen');
	});
	jQuery('.tabbox .tabs').on('click','li a',function(e) {
		e.preventDefault();
		
		location.hash = jQuery(this).attr('href');
		
		// clear previous tab
		
		var $tabbox = jQuery(this).closest('.tabbox');
		$tabbox.find('.tabs li.selected').removeClass('selected');
		$tabbox.find('.tabcontents .tabcontent').hide();
		
		var $li = jQuery(this).closest('li');
		$li.addClass('selected');
		var index = $tabbox.find('ul li').index($li);
		
		$tabbox.find('.tabcontents .tabcontent').eq(index).show();
		
		if (jQuery(this).attr('href')=='#tabaddreview') {
			jQuery('#cancel-comment-reply-link').trigger('click');
		}
	});
	
	var originalhash = location.hash;
	if (location.hash=='#comments') {
		location.hash='#tabreviews';
	}
	var iscomment = false;
	if (location.hash.match(/#comment-[0-9]+/)) {		
		location.hash='#tabreviews';
		iscomment = true;
	}
	if (location.hash.substr(0,4)=='#tab' && jQuery('.tabbox').length) {
		jQuery('.tabs li a[href="'+location.hash+'"]').trigger('click');
		jQuery('html,body').scrollTop(jQuery('.tabbox').offset().top);		
	}	
	if (iscomment) {
		location.hash = originalhash;
	} 
	
	var fixedheader = false;
	
	function ouacHeader() {
		var newfixedheader = $window.scrollTop()>128;

		if (newfixedheader != fixedheader) {
			fixedheader = newfixedheader;

			if (fixedheader) $body.addClass('fixedheader');
			else $body.removeClass('fixedheader');
		}		
	}
	
	$window.on('scroll',jQuery.throttle(100,ouacHeader)).triggerHandler('scroll');
	
	jQuery('.featuregrid li a').matchHeight();
	
	jQuery('.postdiv .post-header .reviews>a').click(function(e) {
		e.preventDefault();
		jQuery(this).closest('.reviews').toggleClass('open');
	});
				
	jQuery('.postdiv .post-header .share>a, .postdiv .postbuttons .share>a').click(function(e) {
		e.preventDefault();
		jQuery(this).closest('.share').toggleClass('open');
	});	
	
	jQuery('.postdiv .post-header a[data-tab], .table-of-contents a[data-tab], .ingtable a[data-tab]').click(function(e) {
		e.preventDefault();
		location.hash = jQuery(this).attr('data-tab');
		jQuery('html,body').scrollTop(jQuery('#tabbox').offset().top);
		jQuery('.tabbox .tabs a[href="'+jQuery(this).attr('data-tab')+'"]').trigger('click');		
	});
	
	var metric = false;
	function togglemetric() {
		metric = !metric;		
		if (metric) {
			Cookies.set('metric','1',{expires:3650,path:'/'});
			jQuery('.metrictoggle').removeClass('metrictoggle-cupson');
		} else {
			Cookies.remove('metric',{path:'/'});
			jQuery('.metrictoggle').addClass('metrictoggle-cupson');
		}
		jQuery('.toggleunits').each(function() {
			var alt = jQuery(this).attr('data-alt');
			var cur = jQuery(this).html();
			jQuery(this).html(alt);
			jQuery(this).attr('data-alt',cur);
		});		
	}
	jQuery('.metrictoggle a').click(function(e) {
		e.preventDefault();				
		if (jQuery(this).hasClass('metrictoggle-metric') != metric) togglemetric();
	});
	jQuery('.metrictoggle').css('visibility','visible');
	if (Cookies.get('metric')==1) {
		togglemetric();
	}
	jQuery('.metrictoggle .toggleicon').click(function(e) {
		togglemetric();
	});	
	
	jQuery('.recipediv .disclaimer .disctoggle a, .wprm-recipe-template-ouac-recipe .disclaimer .disctoggle a').click(function(e) {
		e.preventDefault();
		jQuery(this).closest('.disclaimer').toggleClass('open');
	});


	jQuery(document).click(function(event) { 
		var $target = jQuery(event.target);
		if (!$target.closest('.postdiv .post-header .share').length) {
			jQuery('.postdiv .post-header .share').removeClass('open');
		}
		if (!$target.closest('.postdiv .postbuttons .share').length) {
			jQuery('.postdiv .postbuttons .share').removeClass('open');
		}		
		if (!$target.closest('.postdiv .post-header .reviews').length) {
			jQuery('.postdiv .post-header .reviews').removeClass('open');
		}
		if (!$target.closest('#searchbar').length && !$target.hasClass('togglesearch')) {
			$body.removeClass('searchopen');
		}		
	});	
	
	var $starinput = jQuery('#respond input[name="ratingselect"]');
	if ($starinput.length) {
		var $stars = jQuery('#respond .rating-stars-rate').find('.star');
		
		function ouacShowRating(rating) {
			$stars.each(function(index,value) {
				if (index<rating) {
					jQuery(this).removeClass('star-off').addClass('star-on');
				} else {
					jQuery(this).removeClass('star-on').addClass('star-off');
				}
			});
		}
		
		// page load
		ouacShowRating($starinput.val());
	
		jQuery('#respond .rating-stars-rate .rating-stars-a').on('mouseenter','.star',function(e) {
			var rating = $stars.index(jQuery(this))+1;
			ouacShowRating(rating);
		}).on('mouseleave',function(e) {
			var rating = $starinput.val();
			ouacShowRating(rating);
		}).on('click','.star',function(e) {
			var rating = $stars.index(jQuery(this))+1;
			ouacShowRating(rating);
			$starinput.val(rating);
		});
	}
	
	if (jQuery.isFunction(jQuery.fn.owlCarousel)) {	
		jQuery('.cookbook-slideshow .owl-carousel').owlCarousel({
			items:1,
			margin:0,
			nav:true,
			dots:false
		});	
	}
	
	jQuery('.opencookbookpopup').click(function(e) {
		e.preventDefault();
		var $overlay = jQuery('<div class="popupoverlay"></div>');
		jQuery('body').append($overlay);
		var id = jQuery(this).data('id');
		if (!id) id = '#buypopup';
		var $popup = jQuery(id);
		$popup.find('img[data-src]').each(function() {
			jQuery(this).attr('src',jQuery(this).attr('data-src')).removeAttr('data-src');
		});
		var $close = jQuery('<button class="closebtn"><span class="screen-reader-text">Close</span><span class="icon"></span></button>');

		$popup.prepend($close);

		$overlay.add($close).click(function(e) {
			e.preventDefault();
			$overlay.remove();
			$close.remove();
			$popup.hide();
		});

		$overlay.show();
		$popup.show();
	});	
	
	var $ingredients = jQuery('.tabbox .recipediv .ingredients');
	if ($ingredients.length) {
	
		var ismobile=false;
		(function(a){if(/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(a)||/1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0,4)))ismobile=true;})(navigator.userAgent||navigator.vendor||window.opera);
		
		
		if (ismobile) {
		
			var $textingredients = jQuery('<p class="textingredients"><a class="btn btn-small" href="#">Text Ingredients</a></p>');
			$textingredients.insertAfter($ingredients).find('a.btn').click(function(e) {
				e.preventDefault();
				var $overlay = jQuery('<div class="popupoverlay"></div>');
				jQuery('body').append($overlay);

				var $popup = jQuery('#txtpopup');

				if (!$popup.length) {
					$popup = jQuery('<div id="txtpopup" class="txtpopup"><div class="txtpopup-a"><div class="txtpopup-header"><h2>Select Ingredients</h2><button class="selectall">Select All</button></div><div class="txtpopup-body"></div><div class="txtpopup-footer"><button class="sendtxt">Send Text</button></div></div></div>');

					$popup.find('.txtpopup-body').append($ingredients.clone());

					$popup.find('.ingredients h3').remove();
					$popup.find('.ingredients li').removeAttr('itemprop').wrapInner('<label/>').find('label').prepend('<input type="checkbox" /><span class="checkbox"></span>');

					$popup.find('button.selectall').click(function(e) {
						$popup.find('.ingredients input[type="checkbox"]').prop('checked',true);
					});
					$popup.find('button.sendtxt').click(function(e) {
						var $seling = $popup.find('.ingredients li').has('input:checked');
						if ($seling.length==0) {
							$seling = $popup.find('.ingredients li');
						}
						var recipetitle = jQuery('.tabbox .recipediv h2.fn.tabtitle').text();
						var recipeurl = jQuery('link[rel="canonical"]').attr('href');
						var message = recipetitle+"\n"+recipeurl+"\n\nIngredients:\n";
						$seling.each(function() {
							message += jQuery(this).text()+"\n";
						});

						var url = "sms:?&body=" + encodeURIComponent(message);
						window.open(url, "_system");
					});
					$body.append($popup);
				}

				var $close = jQuery('<button class="closebtn"><span class="screen-reader-text">Close</span><span class="icon"></span></button>');

				$popup.find('.txtpopup-header').prepend($close);

				$overlay.add($close).click(function(e) {
					e.preventDefault();
					$overlay.remove();
					$close.remove();
					$popup.hide();
				});

				$overlay.show();
				$popup.show();			
			});
		}
	}
	
	jQuery('.recipesort select').on('change',function(e) {
		var $recipesort = jQuery(this).closest('.recipesort');
		var ajax = $recipesort.data('ajax');
		var pop = jQuery(this).val()=='popular';
		var url = pop ? $recipesort.attr('data-pop') : $recipesort.attr('data-rec');
		if (ajax) {
			if (typeof __gaTracker === 'function') __gaTracker('send','event','categories','sort',url, {'transport': 'beacon'} );
			jQuery('.recipeajaxwrap').html('').load(url+'?recipeajax=1');
		} else {
			document.location=url+'#recipelist';
		}
	});	
	
	jQuery('body').fitVids();
	
	jQuery('.conversions').on('click','.conv-group>ul>li>a, .conv-group>ul>li>span',function(e) {
		if (jQuery(this).is('span') && !jQuery('.mobdetect').is(':visible')) return;
		e.preventDefault();
		var $li = jQuery(this).closest('li');
		if ($li.hasClass('open')) {
			$li.removeClass('open');
			$li.find('.conv-data').stop().slideUp(300,function() {
				jQuery(this).css('height','');
			});
		} else {
			$li.addClass('open');
			$li.find('.conv-data').stop().slideDown(300,function() {
				jQuery(this).css('height','');
			});
		}
	});
	jQuery('.conversions .conv-search input').on('keyup',function() {
		var value = jQuery(this).val().toLowerCase();

		jQuery('.conversions .conv-results .conv-group').each(function() {
			var found = false;
			var alt = false;
			jQuery(this).find('>ul>li').each(function() {
				var ing = jQuery(this).find('a').text().toLowerCase();
				if (ing.indexOf(value)!=-1) {
					found = true;
					if (alt) jQuery(this).addClass('alt');
					else jQuery(this).removeClass('alt');
					jQuery(this).show();

					alt = !alt;

				}
				else {
					jQuery(this).hide();
				}
			});
			jQuery(this).toggle(found);
		});
	}).triggerHandler('keyup');
    
	jQuery('.table-of-contents .toc-toggle button').on('click',function(e){
		e.preventDefault();
		var $table = jQuery(this).closest('.table-of-contents');		
		$table.addClass('expanded');
		jQuery(this).closest('.toc-toggle').remove();
	});	

	jQuery('.wp-block-yoast-faq-block').on('click','.schema-faq-question',function(e) {
		e.preventDefault();
		jQuery(this).closest('.schema-faq-section').toggleClass('open');
	});    
	
    var preloadedResults = {};
    var observerprev = false;
    var observernext = false;
	var pageobserver = false;
    
    function setPageNav(pagenum) {
        // check this page actually exists
        var $pageel = jQuery('.ajaxresults [data-page='+pagenum+']');
        if ($pageel.length) {
            history.replaceState(null,'',$pageel.data('pageurl'));
        }
    }
    function checkPageNav($el) {
        if (!$el.length) return;
		if (!pageobserver) {
			pageobserver = new IntersectionObserver(
				function(changes) {
					changes.forEach(function(change,index) {
						if (change.isIntersecting) {
							setPageNav(jQuery(change.target).data('page'));
						} else {
							if (change.boundingClientRect.top>0) {
								setPageNav(jQuery(change.target).data('page')-1);
							}
						}
					});
				},
				{ rootMargin: "0px 0px 0px 0px" }
			);
		}
		pageobserver.observe($el.get(0));
    }

	function unsetupAjaxNav() {
		if (observerprev) {observerprev.disconnect();observerprev=false;}
		if (observernext) {observernext.disconnect();observernext=false;}
		if (pageobserver) {pageobserver.disconnect();pageobserver=false;}
		preloadedresults = {}
	}
    
    function setupAjaxNav() {
        $ajaxbtn = jQuery('.ajaxnav');
        if ($ajaxbtn.length) {
            checkPageNav(jQuery('.ajaxresults [data-page]').first());
            (function() {
                function fetchResults($btn) {
                    if ($btn.hasClass('loading') || $btn.hasClass('loaded')) return; // already fetching
    
                    $btn.addClass('loading');
    
                    var url = $btn[0].href;
    
                    var type = $btn.closest('.ajaxnav').hasClass('ajaxcomments') ? 'comments' : 'posts';
                    var params = {
                        ajaxpagination:type
                    };
                        
                    jQuery.ajax({
                        dataType:"json",
                        url:url,
                        data: params,
                        success:function(data) {
                            // make sure btn still exists
                            if ($btn.closest('html').length) {
                                preloadedResults[url] = data;
                                $btn.removeClass('loading');
                                $btn.addClass('loaded');
                                if ($btn.hasClass('clicked')) {
                                    $btn.removeClass('clicked');
                                    $btn.trigger('click');
                                }
                            }
                        }
                    });
                }
    
                $ajaxbtn.each(function() {
                    if (jQuery(this).hasClass('ajaxnav-top')) {
                        observerprev = new IntersectionObserver(
                            function(changes) {
                                changes.forEach(function(change,index) {
                                    if (change.isIntersecting) {
                                        fetchResults(jQuery(change.target).find('a'));
                                    }
                                });
                            },
                            { rootMargin: "500px 0px 0px 0px" }
                        );
    
                        observerprev.observe(jQuery(this).get(0));
                    } else {
                        observernext = new IntersectionObserver(
                            function(changes) {
                                changes.forEach(function(change,index) {
                                    if (change.isIntersecting) {								
                                        fetchResults(jQuery(change.target).find('a'));
                                    }
                                });
                            },
                            { rootMargin: "0px 0px 500px 0px" }
                        );					
                        observernext.observe(jQuery(this).get(0));
                    }
                });
    
                jQuery('.ajaxnav a').click(function(e) {
                    e.preventDefault();
                    var $btn = jQuery(this);
    
                    if ($btn.hasClass('clicked')) return;
                    $btn.addClass('clicked');
    
                    var url = $btn[0].href;
    
                    if ($btn.hasClass('loaded')) {
                        var $location = jQuery('.ajaxresults');
                        
                        var type = $btn.closest('.ajaxnav').hasClass('ajaxcomments') ? 'comments' : 'posts';
    
                        var prev = $btn.closest('.ajaxnav').hasClass('ajaxnav-top');						
    
                        var newpagelink = '';
    
                        var scrollbefore = $window.scrollTop();
                        var scrolloffset = 0;
                        var positionbefore;
    
                        if (prev) {
                            positionbefore = $location.offset().top + $location.height();
                            $location.prepend(preloadedResults[url].html);
                            newpagelink = preloadedResults[url].prevlink;
    
                            checkPageNav($location.find('[data-page]').first());
                        } else {
                            $location.append(preloadedResults[url].html);
                            newpagelink = preloadedResults[url].nextlink;
                            checkPageNav($location.find('[data-page]').last());
                        }
                        if (newpagelink=='') {
                            if (prev) {
                                observerprev.unobserve($btn.closest('.ajaxnav').get(0));
                                observerprev = false;
                            } else {
                                observernext.unobserve($btn.closest('.ajaxnav').get(0));
                                observernext = false;
                            }
                            $btn.closest('.ajaxnav').remove();
                        } else {
                            $btn.attr('href',newpagelink);
                            $btn.removeClass('clicked loaded');
                        }
    
                        if (prev) {
                            var positionafter = $location.offset().top + $location.height();
                            jQuery('body,html').scrollTop(scrollbefore + positionafter - positionbefore);
                        }
    
                        delete preloadedResults[url];
                    } else if (!$btn.hasClass('loading')) {
                        fetchResults(jQuery(this));
                    }
                });
            })();
        } else $ajaxbtn = false;
    }
    
    setupAjaxNav();	
	
	
});