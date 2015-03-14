/**
 * duct front-end core
 */
(function ($) {

    // Create modal alert windows (using Foundation reveal)
    function modal_alert(bodytext, bodytag, headertext) {
        var modal_body;
        if (headertext) {
            $('#modal-header').empty().text(headertext);
        }
        if (bodytext) {
            modal_body = (bodytag) ? $('<' + bodytag + ' />') : $('<p />');
            $('#modal-body').empty().append(
                modal_body.addClass('modal-error-text').text(bodytext)
            );
        }
        $('#modal-ok-box').show();
        $('#modal-dynamic').foundation('reveal', 'open');
    }
    function modal_prompt(prompt, bodytag, headertext) {
        var modal_body;
        if (headertext) {
            $('#modal-header').empty().html(headertext);
        }
        if (prompt) {
            modal_body = (bodytag) ? $('<' + bodytag + ' />') : $('<p />');
            $('#modal-body').empty().append(
                modal_body
                    .addClass('modal-error-text')
                    .append(prompt)
            );
        }
        $('#modal-dynamic').foundation('reveal', 'open');
    }

    function Duct(socket) {
        this.socket = socket;
    }

    // Get all active votes
    Duct.prototype.sync = function () {
        this.socket.emit('sync');
    };
    
    Duct.prototype.intake = function () {
        var self = this;
        this.socket.on('synced', function (res) {
            console.log(res);
        });
        this.socket.on('contract-output', function (res) {
            if (res && res.reputation && res.outcomes && res.reporter_bonus) {
                $('#status-receiver').slideUp('slow');
                var reputation = "Reputation: " + JSON.stringify(res.reputation, null, 3) + "\n";
                var outcomes = "Outcomes: " + JSON.stringify(res.outcomes, null, 3) + "\n";
                var reporter_bonus = "Reporter bonus: " + JSON.stringify(res.reporter_bonus, null, 3);
                var output = $('<pre />').text(reputation + outcomes + reporter_bonus);
                $('#main-receiver').append(output).show();
            } else {
                $('#status-receiver').html("<h4>Contract execution unsuccessful</h4>");
            }
        });
        return this;
    };

    Duct.prototype.exhaust = function () {
        var self = this;

        $('#modal-ok-button').click(function (event) {
            event.preventDefault();
            $('#modal-ok-box').hide();
            $('#modal-dynamic').foundation('reveal', 'close');
        });

        $('form#run-contract-form').submit(function (event) {
            event.preventDefault();
            $('#status-receiver').html('<h4>Running contract...</h4>').show();
            var data = {
                contract_address: $('#contract-address-input').val(),
                gas_input: parseInt($('#gas-input').val()),
                function_name: $('#function-name-input').val()
            };
            self.socket.emit('run-contract', data);
            this.reset();
        });

        // Submit a new question for voting
        $('#new-question').click(function (event) {
            event.preventDefault();
            var answers = '<ul class="plain flush-left" id="answer-list">' +
                '<li><input type="text" id="answer-1" class="possible-answer" value="Yes" required /></li>' +
                '<li><input type="text" id="answer-2" class="possible-answer" value="No" required /></li>' +
                '<li><input type="text" id="answer-3" class="possible-answer" value="Maybe" required /></li>' +
                '</ul>' +
                '<button class="button secondary tiny" id="less-options">-</button>&nbsp;' +
                '<button class="button secondary tiny" id="more-options">+</button>';
            var question = '<form action="#" method="POST" id="new-question-form">' +
                '<input type="text" id="question-text" name="question-text" ' +
                'placeholder="Enter your question here" required autofocus />' +
                '<h5>Possible answers:</h5><div class="row">' + answers + "</div>" +
                '<button type="submit" class="button small" id="submit-question-button">Submit</button>' +
                '</form>';
            modal_prompt(question, "h5", "Propose a question");
            $('#less-options').click(function (event) {
                var num_answers = $('#answer-list').children().length;
                if (num_answers > 1)
                    $('#answer-' + JSON.stringify(num_answers)).parent().remove();
                event.preventDefault();
            });
            $('#more-options').click(function (event) {
                var num_answers = parseInt($('#answer-list').children().length);
                $('<li />').append(
                    $('<input required />')
                        .addClass("possible-answer")
                        .val("")
                        .attr("type", "text")
                        .attr("id", "answer-" + JSON.stringify(num_answers + 1))
                        .attr("placeholder", "Enter answer here...")
                ).appendTo($('#answer-list'));
                event.preventDefault();
            });
            $('form#new-question-form').submit(function (event) {
                event.preventDefault();
                var answers = [];
                $('.possible-answer').each(function () {
                    answers.push(this.value);
                });
                self.socket.emit('submit-question', {
                    question_text: $('#question-text').val(),
                    answers: answers,
                });
                this.reset();
                $('#modal-dynamic').foundation('reveal', 'close');
            });
        });

        return self;
    };

    $(document).ready(function () {
        var socket_url, duct;
        socket_url = window.location.protocol + '//' + document.domain +
            ':' + location.port + '/socket.io/';
        socket = io.connect(socket_url);
        socket.on('connect', function () {
            duct = new Duct(socket);
            duct.intake().exhaust();
        })
    });

})(jQuery);
