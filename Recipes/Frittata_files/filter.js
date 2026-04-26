/*
	* Filter.js
	*
	* @package      sb_filter
	* @author       Lindsay Humes
	* @since        1.0.0
	* @license      GPL-2.0+
*/

jQuery(function ($) {
    //// Accordion
    var allPanels = $('.accordion-content').hide();
    var allButtons = $('.accordion-title');

    $('.accordion-button').click(function () {
        var $this = $(this);
        if ($this.is('.accordion-button-selected')) {
            $this.siblings(".accordion-content").slideUp(500);
            $this.removeClass('accordion-button-selected');
        } else {
            allPanels.slideUp();
            allButtons.removeClass('accordion-button-selected');
            $this.siblings(".accordion-content").slideDown(500);
            $this.addClass('accordion-button-selected');
        }

    });

    var entityMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '/': '&#x2F;',
        '`': '&#x60;',
        '=': '&#x3D;'
    };


    function escapeHtml(string) {
        return String(string).replace(/[&<>"'`=\/]/g, function (s) {
            return entityMap[s];
        });
    }

    $('#filter').change(function (e) {
        var x = e;
        var filter = $('#filter');
        var $checkbox = $(e.target);
        var checked = $checkbox.prop('checked');
        var label = escapeHtml($checkbox.parent().text());
        var $newLabel = $("<span data-label='" + label + "'>" + label + "</span>");
        var $accordionSelected = $(e.target).parents(".accordion-content").siblings(".accordion-selected");
        var $currentLabels = $accordionSelected.find("[data-label='" + label + "']");
        if ($currentLabels.length === 0 && checked) {
            $accordionSelected.prepend($newLabel);
        } else {
            $currentLabels.remove();
        }

        $.ajax({
            url: filter.attr('action'),
            data: filter.serialize(), // form data
            type: filter.attr('get'), // POST
            beforeSend: function (xhr) {
                filter.find('button').text('Processing...'); // changing the button label
            },
            success: function (data) {
                filter.find('button').text('Apply filter'); // changing the button label back
                $('#response').html(data); // insert data
            }
        });
        return false;
    });

    $("#filter").on("reset", function (e) {
        var $this = $(this);
        $this.find(".accordion-selected").empty();
        setTimeout(function () {
            $this.trigger("change");
        });
    });


    // RECIPE FILTER PAGINATION
    $('#response').on('click', '.pagination-filter .page-numbers', function (e) {
        e.preventDefault();

        var $pageNumber = $(e.currentTarget);
        var url = $pageNumber.attr('href');
        $.ajax({
            url: url,
            success: function (data) {
                $('#response').html(data);
                $('html,body').animate({scrollTop: $('#response').offset().top - 200}, 500);
            }
        })
    });

});
