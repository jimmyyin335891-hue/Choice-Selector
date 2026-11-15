
from drafter import *
from dataclasses import dataclass, field
import random as rng
import math
import html


# ==================================================
# 1. WEBSITE SETTINGS
# ==================================================

set_website_title("TinyDecisions")
set_website_style("water")

# This CSS is only used for the wheel and general spacing.
# The rest of the website uses normal Drafter components.

add_website_css(
    "#decision-wheel",
    """
    display: block;
    width: 100%;
    max-width: 430px;
    height: auto;
    margin: 12px auto;
    transform-origin: center center;
    transform-box: fill-box;
    transition: transform 4.2s cubic-bezier(0.12, 0.75, 0.12, 1);
    """
)

add_website_css(
    ".wheel-pointer",
    """
    text-align: center;
    font-size: 34px;
    line-height: 1;
    margin-bottom: -12px;
    position: relative;
    z-index: 2;
    """
)

add_website_css(
    ".wheel-area",
    """
    max-width: 500px;
    margin: 0 auto;
    text-align: center;
    """
)

add_website_css(
    ".result-area",
    """
    padding: 18px;
    margin-top: 18px;
    border-radius: 12px;
    text-align: center;
    background-color: #17365d;
    color: #ffffff;
    font-weight: bold;
    """
)

add_website_css(
    ".result-area *",
    """
    color: #ffffff !important;
    """
)


add_website_css(
    ".method-description",
    """
    margin-top: -8px;
    margin-bottom: 16px;
    """
)

add_website_css(
    ".choice-list",
    """
    padding: 14px;
    border-radius: 10px;
    margin: 12px 0;
    background-color: rgba(120, 140, 160, 0.08);
    """
)



add_website_js(r"""
(function () {
    function animateWheel(wheel) {
        if (!wheel.classList.contains("spinning-wheel")) {
            return;
        }

        if (wheel.dataset.animationStarted === "yes") {
            return;
        }

        const transform = wheel.style.transform ||
                          wheel.getAttribute("transform") || "";
        const match = transform.match(/rotate\(\s*(-?[0-9.]+)/i);

        if (!match) {
            return;
        }

        const targetRotation = Number(match[1]);
        wheel.dataset.animationStarted = "yes";
        wheel.style.transition = "none";
        wheel.style.transform = "rotate(0deg)";

        // Apply the starting position before beginning the transition.
        void wheel.getBoundingClientRect();

        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                wheel.style.transition =
                    "transform 4.2s cubic-bezier(0.12, 0.75, 0.12, 1)";
                wheel.style.transform =
                    "rotate(" + targetRotation + "deg)";
            });
        });
    }

    function scan(root) {
        if (!root) {
            return;
        }

        if (root.matches && root.matches("#decision-wheel")) {
            animateWheel(root);
        }

        if (root.querySelectorAll) {
            root.querySelectorAll("#decision-wheel").forEach(
                animateWheel
            );
        }
    }

    function observeRoot(root) {
        if (!root || root.__tinyDecisionsObserved) {
            return;
        }

        root.__tinyDecisionsObserved = true;
        scan(root);

        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType === 1) {
                        scan(node);
                        if (node.shadowRoot) {
                            observeRoot(node.shadowRoot);
                        }
                    }
                });
            });
        });

        observer.observe(root, {
            childList: true,
            subtree: true
        });

        if (root.querySelectorAll) {
            root.querySelectorAll("*").forEach(function (element) {
                if (element.shadowRoot) {
                    observeRoot(element.shadowRoot);
                }
            });
        }
    }

    function start() {
        observeRoot(document);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
})();
""")


# ==================================================
# 2. CONSTANTS
# ==================================================

WHEEL_COLORS = [
    "#FF7675",
    "#74B9FF",
    "#55EFC4",
    "#FFEAA7",
    "#A29BFE",
    "#FD79A8",
    "#81ECEC",
    "#FAB1A0",
    "#B8E994",
    "#F8C291",
    "#82CCDD",
    "#D6A2E8"
]

MINIMUM_CHOICES = 2
MINIMUM_SCORE = 1
MAXIMUM_SCORE = 5
WHEEL_ANIMATION_TIME = 4200
WHEEL_FULL_TURNS = 5


# ==================================================
# 3. DATA CLASSES
# ==================================================

@dataclass
class DecisionOption:
    """
    Stores information about one choice.

    name:
        The name of the choice entered by the user.

    score:
        The score assigned during Compare Scores.
    """

    name: str
    score: int = 0


@dataclass
class State:
    """
    Stores information that needs to be remembered
    while the user moves between website pages.
    """

    # The question being decided.
    question: str = ""

    # All the choices entered by the user.
    options: list[DecisionOption] = field(default_factory=list)

    # The method currently being used.
    selected_method: str = ""

    # The final selected choice.
    result: str = ""

    # Messages used for errors and instructions.
    message: str = ""

    # Stores the score input for the comparison page.
    score_input: str = ""

    # Wheel animation information.
    wheel_rotation: float = 0.0
    wheel_winner: str = ""
    wheel_spinning: bool = False

    # Stores the number of times the wheel has spun.
    wheel_spin_count: int = 0

    # Stores the result history.
    result_history: list[str] = field(default_factory=list)


# ==================================================
# 4. GENERAL HELPER FUNCTIONS
# ==================================================

def get_option_names(state: State) -> list[str]:
    """
    Return the names of every choice.

    This function loops through the DecisionOption
    objects and collects their names.
    """

    names = []

    for option in state.options:
        names.append(option.name)

    return names


def get_number_of_choices(state: State) -> int:
    """Return how many choices the user has entered."""

    return len(state.options)


def has_enough_choices(state: State) -> bool:
    """Check whether the user has entered enough choices."""

    if len(state.options) >= MINIMUM_CHOICES:
        return True

    return False


def clear_previous_result(state: State) -> None:
    """Clear information from the previous decision method."""

    state.result = ""
    state.selected_method = ""
    state.message = ""
    state.score_input = ""


def add_result_to_history(state: State) -> None:
    """Save the current result in the result history."""

    if state.result != "":
        history_entry = (
            state.selected_method + ": " + state.result
        )

        state.result_history.append(history_entry)


def create_navigation() -> list:
    """
    Create the navigation buttons used on most pages.
    """

    return [
        HorizontalRule(),
        Button("Home", "index"),
        Button("Edit Choices", "create"),
        Button("Methods", "methods")
    ]


def create_page_heading(title: str) -> list:
    """Create the consistent heading used across pages."""

    return [
        Header("TinyDecisions"),
        Header(title),
        HorizontalRule()
    ]


def create_choice_display(state: State) -> list:
    """
    Display the user's choices in numbered order.

    This uses a loop so any number of choices can
    be displayed without creating separate code
    for each choice.
    """

    choice_components = []

    for index, option in enumerate(state.options):
        choice_text = (
            str(index + 1) + ". " + option.name
        )

        choice_components.append(choice_text)

    return choice_components


def show_choice_requirement(state: State) -> Page:
    """Send the user back to the choice page if needed."""

    state.message = (
        "Please enter at least two choices before "
        "using a decision method."
    )

    return create(state)


# ==================================================
# 5. LET US CHOOSE HELPER FUNCTIONS
# ==================================================

def generate_letter_weights() -> dict[str, int]:
    """
    Give each letter a randomly generated value.

    The values are used internally by Let Us Choose.
    They are not displayed to the user.
    """

    weights = {}

    for letter in "abcdefghijklmnopqrstuvwxyz":
        weights[letter] = rng.randint(1, 100)

    return weights


def calculate_option_average(
    option: DecisionOption,
    weights: dict[str, int]
) -> float:
    """
    Calculate the average value of the letters
    in one choice.
    """

    total = 0
    letter_count = 0

    for letter in option.name.lower():

        if letter in weights:
            total += weights[letter]
            letter_count += 1

    if letter_count == 0:
        return 0.0

    return total / letter_count


def calculate_mystery_pick(state: State) -> str:
    """
    Select a choice using the Let Us Choose method.

    The user only sees the final selected choice.
    """

    weights = generate_letter_weights()

    highest_average = -1.0
    winners = []

    for option in state.options:

        average = calculate_option_average(
            option,
            weights
        )

        if average > highest_average:
            highest_average = average
            winners = [option.name]

        elif average == highest_average:
            winners.append(option.name)

    if len(winners) == 0:
        return rng.choice(get_option_names(state))

    return rng.choice(winners)


# ==================================================
# 6. WHEEL DRAWING HELPER FUNCTIONS
# ==================================================

def calculate_wheel_point(
    angle: float,
    radius: float
) -> tuple[float, float]:
    """
    Calculate an x and y coordinate on the wheel.

    This is used to create the wheel's colored sections.
    """

    radians = math.radians(angle)

    x = 200 + radius * math.cos(radians)
    y = 200 + radius * math.sin(radians)

    return x, y


def create_wheel_section(
    index: int,
    total_options: int,
    color: str,
    label: str
) -> str:
    """
    Create one colored section of the SVG wheel.

    Each section represents one user choice.
    """

    angle_per_choice = 360 / total_options

    start_angle = (
        -90 + index * angle_per_choice
    )

    end_angle = start_angle + angle_per_choice

    start_x, start_y = calculate_wheel_point(
        start_angle,
        180
    )

    end_x, end_y = calculate_wheel_point(
        end_angle,
        180
    )

    middle_angle = (
        start_angle + end_angle
    ) / 2

    label_x, label_y = calculate_wheel_point(
        middle_angle,
        115
    )

    large_arc = 1 if angle_per_choice > 180 else 0

    path = (
        "M 200 200 "
        + "L " + str(start_x) + " " + str(start_y)
        + " A 180 180 0 "
        + str(large_arc)
        + " 1 "
        + str(end_x) + " " + str(end_y)
        + " Z"
    )

    safe_label = html.escape(label)

    # Shorten very long labels so they fit on the wheel.
    if len(safe_label) > 17:
        safe_label = safe_label[:14] + "..."

    section = (
        '<path d="' + path + '" '
        'fill="' + color + '" '
        'stroke="white" '
        'stroke-width="3"/>'
    )

    section += (
        '<text x="' + str(label_x) + '" '
        'y="' + str(label_y) + '" '
        'text-anchor="middle" '
        'dominant-baseline="middle" '
        'font-size="13" '
        'font-weight="bold" '
        'fill="#222222">'
        + safe_label
        + "</text>"
    )

    return section


def create_wheel_graphic(state: State) -> str:
    """
    Build the complete wheel using SVG shapes.

    The SVG is only used for the wheel graphic.
    The rest of the website uses Drafter components.
    """

    total_options = len(state.options)

    drawing = ""

    # Create a section for every choice.
    for index, option in enumerate(state.options):

        color = WHEEL_COLORS[
            index % len(WHEEL_COLORS)
        ]

        drawing += create_wheel_section(
            index,
            total_options,
            color,
            option.name
        )

    # Add the center of the wheel.
    drawing += (
        '<circle cx="200" cy="200" r="17" '
        'fill="#333333" stroke="white" stroke-width="3"/>'
    )

    # Add an outer border.
    drawing += (
        '<circle cx="200" cy="200" r="180" '
        'fill="none" stroke="#333333" stroke-width="5"/>'
    )

    return drawing


def calculate_wheel_rotation(
    state: State,
    winner_index: int
) -> float:
    """
    Calculate how far the wheel must rotate.

    The selected choice will end up underneath
    the fixed pointer at the top of the wheel.
    """

    total_options = len(state.options)

    angle_per_choice = 360 / total_options

    middle_angle = (
        winner_index + 0.5
    ) * angle_per_choice - 90

    desired_angle = (-90 - middle_angle) % 360

    current_angle = state.wheel_rotation % 360

    additional_rotation = (
        desired_angle - current_angle
    ) % 360

    full_rotation = (
        WHEEL_FULL_TURNS * 360
    )

    return (
        state.wheel_rotation
        + full_rotation
        + additional_rotation
    )


def create_wheel_component(state: State) -> SVG:
    """
    Create the Drafter SVG component.

    The CSS transition animates the wheel when
    its rotation value changes.
    """

    return SVG(
        create_wheel_graphic(state),
        width=400,
        height=400,
        viewBox="0 0 400 400",
        id="decision-wheel",
        classes=(
            "spinning-wheel"
            if state.wheel_spinning
            else "decision-wheel"
        ),
        style_transform=(
            "rotate(" + str(state.wheel_rotation) + "deg)"
        )
    )


# ==================================================
# 7. ROUTE 1: HOMEPAGE
# ==================================================

@route
def index(state: State) -> Page:
    """Display the main homepage."""

    return Page(state, [
        *create_page_heading("Make Your Decision"),

        Paragraph(
            "Can't decide what to choose? "
            "TinyDecisions is here to help!"
        ),

        Paragraph(
            "Enter your question, add as many choices as "
            "you want, and let one of our decision methods "
            "help you decide."
        ),

        HorizontalRule(),

        Header("How It Works"),

        NumberedList([
            "Enter the question you are trying to answer.",
            "Add all the choices you are considering.",
            "Choose your favorite decision method.",
            "See which choice gets selected!"
        ]),

        HorizontalRule(),

        Header("Your Current Decision"),

        Paragraph(
            "Question: "
            + (
                state.question
                if state.question != ""
                else "No question entered yet."
            )
        ),

        Paragraph(
            "Number of choices: "
            + str(get_number_of_choices(state))
        ),

        Paragraph(
            "Previous result: "
            + (
                state.result
                if state.result != ""
                else "No result yet."
            )
        ),

        Button("Start a Decision", "create"),

        Button("Choose a Method", "methods"),

        *create_navigation()
    ])


# ==================================================
# 8. ROUTE 2: CREATE A DECISION
# ==================================================

@route
def create(state: State) -> Page:
    """Display the form for creating a decision."""

    return Page(state, [
        *create_page_heading("Create Your Decision"),

        Paragraph(
            "Start by entering the question you need help "
            "answering."
        ),

        "Your question:",

        TextBox(
            "question",
            state.question,
            placeholder="Example: What should I eat?"
        ),

        HorizontalRule(),

        Header("Enter Your Choices"),

        Paragraph(
            "Enter each choice on a separate line. "
            "There is no fixed limit on the number of choices."
        ),

        Paragraph(
            "Example:\nPizza\nBurgers\nTacos\nSushi"
        ),

        TextArea(
            "choices",
            "\n".join(get_option_names(state)),
            rows=10,
            placeholder="Enter one choice per line..."
        ),

        Paragraph(state.message),

        Button("Save My Choices", "save_choices"),

        *create_navigation()
    ])


@route
def save_choices(
    state: State,
    question: str,
    choices: str
) -> Page:
    """
    Save the user's question and choices.

    Blank choices are ignored. At least two valid
    choices are required.
    """

    cleaned_question = question.strip()

    if cleaned_question == "":
        state.message = "Please enter a question."
        return create(state)

    new_options = []

    # Loop through every line in the user's input.
    for line in choices.splitlines():

        cleaned_choice = line.strip()

        if cleaned_choice != "":
            new_options.append(
                DecisionOption(cleaned_choice)
            )

    if len(new_options) < MINIMUM_CHOICES:
        state.message = (
            "Please enter at least two nonblank choices."
        )
        return create(state)

    # Update the saved state.
    state.question = cleaned_question
    state.options = new_options

    clear_previous_result(state)

    state.wheel_rotation = 0.0
    state.wheel_winner = ""
    state.wheel_spinning = False
    state.wheel_spin_count = 0
    state.result_history = []

    return Page(state, [
        *create_page_heading("Choices Saved!"),

        Paragraph(
            "Your question: " + state.question
        ),

        Header("Your Choices"),

        NumberedList(get_option_names(state)),

        Paragraph(
            "You entered "
            + str(len(state.options))
            + " choices."
        ),

        Button("Choose a Method", "methods"),

        Button("Edit Choices", "create"),

        *create_navigation()
    ])


# ==================================================
# 9. ROUTE 3: METHOD SELECTION
# ==================================================

@route
def methods(state: State) -> Page:
    """Display all available decision methods."""

    if not has_enough_choices(state):
        return show_choice_requirement(state)

    return Page(state, [
        *create_page_heading("Choose Your Method"),

        Paragraph(
            "Choose one of the four ways to make "
            "your decision."
        ),

        Header("1. Wheel"),

        Paragraph(
            "A colorful wheel containing all your choices. "
            "Spin it and see where it lands."
        ),

        Button("Open the Wheel", "wheel"),

        HorizontalRule(),

        Header("2. Randomizer"),

        Paragraph(
            "Every choice has an equal chance of being "
            "selected."
        ),

        Button("Open Randomizer", "random"),

        HorizontalRule(),

        Header("3. Let Us Choose"),

        Paragraph(
            "A surprise selection method that chooses "
            "one of your options."
        ),

        Button("Let Us Choose", "gamble"),

        HorizontalRule(),

        Header("4. Compare Scores"),

        Paragraph(
            "Rate your choices from 1 to 5 and see "
            "which one receives the highest score."
        ),

        Button("Open Compare Scores", "compare"),

        *create_navigation()
    ])


# ==================================================
# 10. ROUTE 4: WHEEL PAGE
# ==================================================

@route
def wheel(state: State) -> Page:
    """Display the animated decision wheel."""

    if not has_enough_choices(state):
        return show_choice_requirement(state)

    content = [
        *create_page_heading("Decision Wheel"),

        Paragraph(
            "Give the wheel a spin and let it choose "
            "one of your options."
        ),

        Div(
            [
                Paragraph("▼", classes="wheel-pointer"),
                create_wheel_component(state)
            ],
            classes="wheel-area"
        )
    ]

    # Display a timer while the wheel is spinning.
    if state.wheel_spinning:

        content.extend([
            Header("The wheel is spinning..."),

            Paragraph(
                "Wait for the wheel to finish!"
            ),

            Timer(
                WHEEL_ANIMATION_TIME,
                "finish_wheel",
                show=False
            )
        ])

    else:

        if (
            state.selected_method == "Wheel"
            and state.result != ""
        ):

            content.extend([
                Div(
                    [
                        Header("The Wheel Selected:"),
                        Header(state.result)
                    ],
                    classes="result-area"
                )
            ])

        content.append(
            Button("Spin the Wheel!", "spin_wheel")
        )

    content.extend([
        HorizontalRule(),
        Header("Choices on the Wheel"),
        NumberedList(get_option_names(state)),
        *create_navigation()
    ])

    return Page(state, content)


@route
def spin_wheel(state: State) -> Page:
    """
    Select a random winner and start the wheel animation.

    The selected choice is calculated before the
    animation begins so the wheel can stop on it.
    """

    if not has_enough_choices(state):
        return show_choice_requirement(state)

    if state.wheel_spinning:
        return wheel(state)

    winner_index = rng.randrange(
        len(state.options)
    )

    # Start each spin at zero so the browser can animate it reliably.
    state.wheel_rotation = 0.0

    state.wheel_winner = (
        state.options[winner_index].name
    )

    state.wheel_rotation = calculate_wheel_rotation(
        state,
        winner_index
    )

    state.wheel_spinning = True
    state.selected_method = "Wheel"
    state.result = ""

    state.wheel_spin_count += 1

    return wheel(state)


@route
def finish_wheel(state: State) -> Page:
    """
    Finish the wheel animation and reveal the winner.

    This route is called automatically by the Timer.
    """

    state.wheel_spinning = False

    state.result = state.wheel_winner

    add_result_to_history(state)

    return wheel(state)


# ==================================================
# 11. ROUTE 5: RANDOMIZER PAGE
# ==================================================

@route
def random(state: State) -> Page:
    """Display the Randomizer page."""

    if not has_enough_choices(state):
        return show_choice_requirement(state)

    content = [
        *create_page_heading("Randomizer"),

        Paragraph(
            "The Randomizer gives each of your choices "
            "an equal chance of being selected."
        ),

        Header("Your Choices"),

        NumberedList(get_option_names(state))
    ]

    if (
        state.selected_method == "Randomizer"
        and state.result != ""
    ):

        content.extend([
            Div(
                [
                    Header("Your Random Choice:"),
                    Header(state.result)
                ],
                classes="result-area"
            )
        ])

    content.extend([
        Button("Pick a Random Choice", "random_pick"),

        Button("Try Again", "random_pick"),

        *create_navigation()
    ])

    return Page(state, content)


@route
def random_pick(state: State) -> Page:
    """Choose one of the available choices randomly."""

    if not has_enough_choices(state):
        return show_choice_requirement(state)

    winner = rng.choice(state.options)

    state.selected_method = "Randomizer"
    state.result = winner.name

    add_result_to_history(state)

    return random(state)


# ==================================================
# 12. ROUTE 6: LET US CHOOSE PAGE
# ==================================================

@route
def gamble(state: State) -> Page:
    """Display the Let Us Choose page."""

    if not has_enough_choices(state):
        return show_choice_requirement(state)

    content = [
        *create_page_heading("Let Us Choose"),

        Paragraph(
            "Want to try something different? "
            "Let TinyDecisions surprise you!"
        ),

        Header("Your Choices"),

        NumberedList(get_option_names(state))
    ]

    if (
        state.selected_method == "Let Us Choose"
        and state.result != ""
    ):

        content.extend([
            Div(
                [
                    Header(state.result),
                    Header(state.result)
                ],
                classes="result-area"
            )
        ])

    content.extend([
        Button("Choose For Me", "mystery_pick"),

        Button("Choose Again", "mystery_pick"),

        *create_navigation()
    ])

    return Page(state, content)


@route
def mystery_pick(state: State) -> Page:
    """Run the Let Us Choose selection method."""

    if not has_enough_choices(state):
        return show_choice_requirement(state)

    state.selected_method = "Let Us Choose"

    state.result = calculate_mystery_pick(state)

    add_result_to_history(state)

    return gamble(state)


# ==================================================
# 13. ROUTE 7: COMPARE SCORES PAGE
# ==================================================

@route
def compare(state: State) -> Page:
    """Display the Compare Scores page."""

    if not has_enough_choices(state):
        return show_choice_requirement(state)

    content = [
        *create_page_heading("Compare Scores"),

        Paragraph(
            "Rate each choice from 1 to 5 based on "
            "how much you want that option."
        ),

        Paragraph(
            "A score of 1 means you like the choice the least. "
            "A score of 5 means you like it the most."
        ),

        Header("Your Choices"),

        NumberedList(get_option_names(state)),

        HorizontalRule(),

        Header("Enter Your Scores"),

        Paragraph(
            "Enter exactly one score for each choice. "
            "Keep the scores in the same order as the list."
        ),

        Paragraph(
            "Separate your scores with commas."
        ),

        Paragraph(
            "Example: If your choices are Pizza, Burgers, "
            "and Tacos, you could enter: 5, 3, 4"
        ),

        TextBox(
            "scores",
            state.score_input,
            placeholder="Example: 5, 3, 4"
        ),

        Paragraph(state.message),

        Button("Compare My Scores", "calculate_compare")
    ]

    # Display the score breakdown after submission.
    if (
        state.selected_method == "Compare Scores"
        and state.result != ""
    ):

        content.extend([
            HorizontalRule(),

            Header("Your Score Breakdown")
        ])

        for index, option in enumerate(state.options):

            content.append(
                str(index + 1)
                + ". "
                + option.name
                + " — "
                + str(option.score)
                + "/5"
            )

        content.extend([
            Div(
                [
                    Header("Your Result:"),
                    Header(state.result)
                ],
                classes="result-area"
            )
        ])

    content.extend(create_navigation())

    return Page(state, content)


@route
def calculate_compare(
    state: State,
    scores: str
) -> Page:
    """
    Check the scores and calculate the winner.

    The user must enter exactly one whole number
    between 1 and 5 for every choice.
    """

    state.score_input = scores
    state.message = ""

    score_parts = scores.split(",")

    # Check that the number of scores is correct.
    if len(score_parts) != len(state.options):

        state.message = (
            "Please enter exactly one score for every choice."
        )

        return compare(state)

    converted_scores = []

    # Convert each score into an integer.
    for part in score_parts:

        cleaned_part = part.strip()

        if cleaned_part == "":
            state.message = (
                "One of your scores is blank. "
                "Please fill in every score."
            )

            return compare(state)

        try:
            score = int(cleaned_part)

        except ValueError:

            state.message = (
                "Please enter whole numbers only."
            )

            return compare(state)

        # Make sure each score is within the allowed range.
        if (
            score < MINIMUM_SCORE
            or score > MAXIMUM_SCORE
        ):

            state.message = (
                "Every score must be between 1 and 5."
            )

            return compare(state)

        converted_scores.append(score)

    # Save each score in its matching DecisionOption.
    for index, option in enumerate(state.options):

        option.score = converted_scores[index]

    # Find the highest score.
    highest_score = max(converted_scores)

    winners = []

    # Find every choice with the highest score.
    for option in state.options:

        if option.score == highest_score:
            winners.append(option.name)

    state.selected_method = "Compare Scores"

    # Check whether there is one winner or a tie.
    if len(winners) == 1:

        state.result = winners[0]

    else:

        state.result = (
            "Tie between: " + ", ".join(winners)
        )

    state.message = ""

    add_result_to_history(state)

    return compare(state)


# ==================================================
# 14. RESULT HISTORY PAGE CONTENT
# ==================================================

@route
def history(state: State) -> Page:
    """Display the results from previous selections."""

    content = [
        *create_page_heading("Decision History"),

        Paragraph(
            "Here are the results from your current session."
        )
    ]

    if len(state.result_history) == 0:

        content.append(
            Paragraph("You haven't made any decisions yet.")
        )

    else:

        content.append(
            NumberedList(state.result_history)
        )

    content.extend([
        Button("Back to Home", "index"),
        Button("Choose Another Method", "methods"),
        *create_navigation()
    ])

    return Page(state, content)


# ==================================================
# 15. RESET PAGE
# ==================================================

@route
def reset(state: State) -> Page:
    """Clear the current decision and start over."""

    state.question = ""
    state.options = []
    state.selected_method = ""
    state.result = ""
    state.message = ""
    state.score_input = ""

    state.wheel_rotation = 0.0
    state.wheel_winner = ""
    state.wheel_spinning = False
    state.wheel_spin_count = 0

    state.result_history = []

    return Page(state, [
        *create_page_heading("Start Fresh"),

        Paragraph(
            "Your previous decision has been cleared."
        ),

        Button("Create a New Decision", "create"),

        Button("Return Home", "index")
    ])


# ==================================================
# 16. SITE INFORMATION
# ==================================================

set_site_information(
    "Your Name",
    (
        "TinyDecisions is a website that helps users "
        "make decisions by offering several different "
        "ways to select between their choices."
    ),
    (
        "Drafter documentation: "
        "https://drafter-edu.github.io/drafter/"
    ),
    (
        "See the Final Project Design Phase document "
        "in the project repository."
    ),
    []
)


# ==================================================
# 17. START THE WEBSITE
# ==================================================

start_server(State())
