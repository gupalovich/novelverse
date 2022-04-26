/* Project specific Javascript goes here. */

(function () {

// Tooltip
$('[data-toggle="tooltip"]').tooltip()


// Dom Reverse
$.fn.reverseChildren = function() {
};
$('.js-filter-reverse').on('click', function (e) {
      return $('.js-reverse-content').each(function(){
        var $this = $(this);
        $this.children().each(function(){ $this.prepend(this) });
      });
});


// Global vars
let wto;
const ajaxDelay = 200
const ajaxDelaySearch = 250


// Infinite Scroll
let scrollThreshold = location.pathname === "/" ? false : true;
let scrollHistory = location.pathname === "/" ? false : true;
$('.infinite-container').infiniteScroll({
    path: '.infinite-more-link',
    append: '.infinite-item',
    button: '.infinite-more-link',
    scrollThreshold: scrollThreshold,
    status: '.loading',
    history: scrollHistory,
});


// Select
let selectOptions = {}

$('select').selectize(selectOptions);
// disable search
$('.selectize-input > input').prop('disabled', 'disabled');

// Swiper Slider config
let slides = window.innerWidth > 1750 ? 'auto' : 'auto'
let slideDepth = window.innerWidth > 2020 ? 300 : 500
let swiperOpts = {
    // pagination: {
    //     el: '.swiper-pagination',
    //     dynamicBullets: true,
    // },
    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
      },
    autoplay: {
        delay: 10000,
        disableOnInteraction: true,
    },
    roundLengths: true,
    centeredSlides: true,
    loop: true,
    slidesPerView: slides,
    effect: 'coverflow',
    coverflowEffect: {
        rotate: 0,
        stretch: 0,
        depth: slideDepth,
        modifier: 1,
        slideShadows: false,
    },
    //preventClicks: false,
    //preventClicksPropagation: false,
    slideToClickedSlide: true,
}
let swiper = new Swiper('.swiper-container', swiperOpts);
let swiper_tape = new Swiper('.swiper-tape-container', {
    slidesPerView: 'auto',
    autoplay: {
        delay: 15000,
        disableOnInteraction: true,
    },
    roundLengths: true,
    spaceBetween: 15,
    pagination: {
        el: '.swiper-pagination',
        clickable: true,
    },
});
$('.swiper-fadein').animate({opacity: 1.0}, 300)



// Global Toggle next
$(".js-toggle-next").on('click', function () {
    let btn = $(this);
    btn.next().toggle();
})


// Comments
$("#id_comment").on('click', function () {
    $(this)[0].classList.add('active');
})


// Tags nav
$(".tags-dropdown").on('click', function() {
    $('.js-tags-nav').slideToggle(300);
});


// Form filters
$(".filters-dropdown").on('click', function() {
    $('.js-filter-form').slideToggle(300);
});

$(".js-filter-form").change(function() {
    $(this).submit();
});

// Static Livesearch
$('.js-livesearch-container .js-livesearch-item').each(function() {
    $(this).attr('data-search-term', $(this).text().toLowerCase().replace(/(?:\r\n|\r|\n| )/g, '').trim());
});
$('.js-livesearch-input').on('keyup', function() {
    var searchTerm = $(this).val().toLowerCase();
    if (searchTerm) {
        $('.js-livesearch-container .js-livesearch-item').each(function() {
            if ($(this).filter('[data-search-term *= ' + searchTerm + ']').length > 0 || searchTerm.length < 1) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    } else {
        $('.js-livesearch-container .js-livesearch-item').each(function() {
            $(this).show();
        });
    }
});


// Notifications
function eventNotification(msg='', flag='info') {
    let body = document.body;
    let container = document.getElementsByClassName('container')[1]
    let alertBox = document.createElement('div')
    let alertTime = 2000
    let alertTimeAnim = alertTime - 200
    alertBox.className = `alert alert-${flag}`
    alertBox.textContent = msg
    container.appendChild(alertBox)
    setTimeout(() => {
        alertBox.classList.add('animate')
    }, 100)
    setTimeout(() => {
        alertBox.classList.remove('animate')
    }, alertTimeAnim)
    setTimeout(() => {
        container.removeChild(alertBox)
    }, alertTime);
}


// CSRF
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
let csrf_form = $("[name=csrfmiddlewaretoken]").val()
let csrftoken = csrf_form ? csrf_form : getCookie('csrftoken');

// Setup ajax connections safely
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


// Ajax book chaps
function getChapsAjax(btn) {
  let loaded = btn.attr("data-loaded");
  if (!!+loaded) {
    return false
  }
  $.ajax({
    url: btn.attr("data-url-chaps"),
    type: "get",
    dataType: "json",
    success: function (data) {
      $('.js-chap-container').html(data['html_chaps']);
      btn.attr("data-loaded", 1);
      if (btn[0].classList.contains('chaps--toggle')) {
          let activeChap = document.getElementById('activeChap')
          activeChap.scrollIntoView(false);
      }
    },
    error: function (xhr, errmsg, err) {
        let msg = `${xhr.status} ${xhr.statusText}`
        eventNotification(msg, 'error')
    },
  });
}

$('.js-load-chaps').on('click', function (e) {
    let btn = $(this);
    getChapsAjax(btn);
})


// Ajax theming
function themeStylesPost(btn) {
    data = {}
    let btn_tm_color = btn.attr("data-theme-color")
    let btn_tm_font = btn.attr("data-theme-font")
    let btn_tm_fz = btn.attr("data-theme-fz")
    let btn_tm_lh = btn.attr("data-theme-lh")
    if (btn_tm_color) {
        data['tm_color'] = btn_tm_color
    }
    if (btn_tm_font) {
        data['tm_font'] = btn_tm_font
    }
    if (btn_tm_fz) {
        data['tm_fz'] = btn_tm_fz
    }
    if (btn_tm_lh) {
        data['tm_lh'] = btn_tm_lh
    }
    $.ajax({
        url: btn.attr("data-theme-url"),
        type: "post",
        dataType: "json",
        data: data,
        success: function (data) {
            // console.log(data)
        },
        error: function (xhr, errmsg, err) {
            let msg = `${xhr.status} ${xhr.statusText}`
            eventNotification(msg, 'error')
        },
    });
}
$(".js-theme").click(function () {
    let btn = $(this);
    wto = setTimeout(function() {
        themeStylesPost(btn);
    }, ajaxDelay);
})


// Ajax Votes
function vote_post(btn) {
    $.ajax({
        url: btn.attr("data-vote-url"),
        type: "post",
        dataType: "json",
        success: function (data) {
            if (data.is_valid) {
                btn.parent().parent().find('.js-bvotes').html(data.book_votes)
                $(".js-uvotes").html(data.user_votes)
                eventNotification('Successfully voted')
            } else {
                eventNotification(data.info_msg, 'warning');
            }
        },
        error: function (xhr, errmsg, err) {
            let msg = `${xhr.status} ${xhr.statusText}`
            eventNotification(msg, 'error')
        },
    });
}

$(document).on('click', '.js-vote-btn', function () {
    let btn = $(this);
    wto = setTimeout(function() {
        vote_post(btn);
    }, ajaxDelay);
})


// Ajax library
function library_post(btn) {
    let data = {
        'lib_in': btn.attr("data-lib-in"),
    }
    console.log(data)
    $.ajax({
        url: btn.attr("data-lib-url"),
        type: "post",
        dataType: "json",
        data: data,
        success: function (data) {
            if (data.is_valid) {
                if (!data.in_lib) {
                    if (btn[0].hasAttribute("data-bookmark")) {
                        btn.html('<i class="fas fa-bookmark"></i>');
                    } else {
                        btn.html('<i class="fas fa-check"></i> In Library');
                    }
                    btn.attr("data-lib-in", 1);
                    eventNotification('Book added to Library');
                } else {
                    if (btn[0].hasAttribute("data-bookmark")) {
                        btn.html('<i class="far fa-bookmark"></i>')
                    } else if (btn[0].hasAttribute("data-lib-remonly")) {
                        btn.parents()[3].remove();
                    } else {
                        btn.html('Add to Library')
                    }
                    btn.attr("data-lib-in", 0)
                    eventNotification('Book removed from Library')
                }
            } else {
                eventNotification(data.info_msg, 'warning');
            }
        },
        error: function (xhr, errmsg, err) {
            let msg = `${xhr.status} ${xhr.statusText}`
            eventNotification(msg, 'error')
        },
    });
}

$(document).on('click', '.js-lib-btn', function () {
    clearTimeout(wto);
    let btn = $(this);
    wto = setTimeout(function() {

        if (btn[0].hasAttribute("data-lib-remonly")) {
            if (confirm('Are you sure you want to remove this book?')) {
                library_post(btn);
            } else {
                return false;
            }
        } else {
            library_post(btn);
        }

    }, ajaxDelay);
})


// Ajax Search
function search_post(form) {
    $.ajax({
        url : form.attr('action'),
        type : "get",
        dataType: "json",
        data : {
            'search_field': $('#id_search_field').val()
        },
        success : function(resp) {
            // $('#id_search_field').val('');
            // $('.booksearch__formresult')[0].classList.add('animate')
            $('.booksearch__formresult').html(resp.html_search_form_result)
        },
        error : function (xhr, errmsg, err) {
            let msg = `${xhr.status} ${xhr.statusText}`
            eventNotification(msg, 'error')
        }
    });
};

// enter keypress disable
// $('#search-form').on('keyup keypress', function(e) {
//     let keyCode = e.keyCode || e.which;
//     if (keyCode === 13) {
//         e.preventDefault();
//         return false;
//     }
// });
$('#search-form').on('change paste keyup', function(e){
    e.preventDefault();
    clearTimeout(wto);
    let form = $(this);

    if ($('#id_search_field').val()) {
        wto = setTimeout(function() {
            search_post(form);
        }, ajaxDelaySearch);
    }
    return false;
});

$.fn.focusTextToEnd = function(){
    this.focus();
    var $thisVal = this.val();
    this.val('').val($thisVal);
    return this;
}
$('#id_search_field').focusTextToEnd();


})();

