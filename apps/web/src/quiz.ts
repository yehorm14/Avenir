export type Question = {
  id: string;
  theme: string;
  title: string;
  hint: string;
  options: { text: string; detail: string; tags: string[] }[];
};
export const questions: Question[] = [
  {
    id: "curiosity",
    theme: "What draws you in",
    title: "You have an afternoon to follow your curiosity. Where do you go?",
    hint: "Choose what you would actually enjoy, even if you're new to it.",
    options: [
      {
        text: "Work out how something works",
        detail: "A system, a machine, a piece of code",
        tags: ["computers_coding", "engineering_making", "security_puzzles"],
      },
      {
        text: "Make something look and feel better",
        detail: "A space, a design, a visual idea",
        tags: ["art_drawing", "design", "building_spaces"],
      },
      {
        text: "Understand and help someone",
        detail: "Listen, explain, or make life a little easier",
        tags: ["helping_people", "teaching_explaining", "science_health"],
      },
      {
        text: "Spot a pattern others missed",
        detail: "In numbers, behaviour, or a business",
        tags: ["maths", "data", "money_business"],
      },
    ],
  },
  {
    id: "challenge",
    theme: "How you think",
    title:
      "When a difficult problem lands in front of you, what comes naturally?",
    hint: "Think about a real project at school, work, or home.",
    options: [
      {
        text: "Break it into small, logical pieces",
        detail: "Understand the rules before finding the answer",
        tags: ["maths", "computers_coding", "security_puzzles"],
      },
      {
        text: "Sketch a few different possibilities",
        detail: "See the bigger picture and try a fresh angle",
        tags: ["design", "art_drawing", "building_spaces"],
      },
      {
        text: "Talk it through with people",
        detail: "Find out what they need and bring them together",
        tags: ["helping_people", "teaching_explaining", "money_business"],
      },
      {
        text: "Try something and see what happens",
        detail: "Learn by building, testing, and improving",
        tags: ["fixing_hands_on", "engineering_making", "electricity_energy"],
      },
    ],
  },
  {
    id: "impact",
    theme: "What matters to you",
    title: "Which kind of difference would feel most worthwhile?",
    hint: "There isn't a more impressive answer. Pick what matters to you.",
    options: [
      {
        text: "Help people live healthier lives",
        detail: "Healthcare, science, and direct support",
        tags: ["science_health", "helping_people"],
      },
      {
        text: "Make places work better",
        detail: "Homes, transport, communities, and clean energy",
        tags: ["building_spaces", "outdoors_maps", "electricity_energy"],
      },
      {
        text: "Build tools that people rely on",
        detail: "Digital services, technology, and useful products",
        tags: ["computers_coding", "design", "security_puzzles"],
      },
      {
        text: "Help people make better decisions",
        detail: "Evidence, education, money, and organisations",
        tags: ["data", "money_business", "teaching_explaining"],
      },
    ],
  },
  {
    id: "team",
    theme: "Your working style",
    title: "In a group, which role do you tend to take?",
    hint: "Choose the role that gives you energy, rather than the one you're expected to fill.",
    options: [
      {
        text: "The person who makes a plan",
        detail: "Organise the work and keep everyone moving",
        tags: ["money_business", "building_spaces"],
      },
      {
        text: "The person who checks the details",
        detail: "Question assumptions and make sure it works",
        tags: ["security_puzzles", "maths", "data"],
      },
      {
        text: "The person with a fresh idea",
        detail: "Imagine alternatives and bring them to life",
        tags: ["design", "art_drawing", "engineering_making"],
      },
      {
        text: "The person who helps everyone contribute",
        detail: "Explain things and notice who needs support",
        tags: ["teaching_explaining", "helping_people", "writing_language"],
      },
    ],
  },
  {
    id: "environment",
    theme: "Your everyday life",
    title: "Which working day sounds more like you?",
    hint: "Imagine an ordinary Tuesday, not the highlight reel.",
    options: [
      {
        text: "Time to focus on a deep problem",
        detail: "Quiet thinking, analysis, and careful progress",
        tags: ["maths", "computers_coding", "data"],
      },
      {
        text: "A mix of people and practical work",
        detail: "Be on your feet and see tangible results",
        tags: ["science_health", "fixing_hands_on", "engineering_making"],
      },
      {
        text: "Moving between places and projects",
        detail: "Real spaces, site visits, and changing surroundings",
        tags: ["outdoors_maps", "building_spaces", "electricity_energy"],
      },
      {
        text: "A collaborative, creative studio",
        detail: "Share ideas and make things with others",
        tags: ["design", "art_drawing", "writing_language"],
      },
    ],
  },
  {
    id: "learn",
    theme: "How you learn",
    title: "You want to learn something unfamiliar. What is your first move?",
    hint: "This helps us suggest a route as well as a career.",
    options: [
      {
        text: "Understand the theory first",
        detail: "Read, investigate, and connect the principles",
        tags: ["maths", "science_health", "data"],
      },
      {
        text: "Build a small version",
        detail: "Experiment and learn from what breaks",
        tags: ["computers_coding", "engineering_making", "fixing_hands_on"],
      },
      {
        text: "Watch someone, then try it",
        detail: "Learn from a mentor and practise together",
        tags: ["helping_people", "teaching_explaining", "electricity_energy"],
      },
      {
        text: "Explore examples and make my own",
        detail: "Collect inspiration and develop a point of view",
        tags: ["art_drawing", "design", "writing_language"],
      },
    ],
  },
  {
    id: "uncertainty",
    theme: "Your motivation",
    title: "What keeps you going when a project gets difficult?",
    hint: "Think about the kind of satisfaction you look for.",
    options: [
      {
        text: "Finally solving the puzzle",
        detail: "A clear answer after patient investigation",
        tags: ["security_puzzles", "maths", "computers_coding"],
      },
      {
        text: "Seeing something I made come to life",
        detail: "A working product or a finished design",
        tags: ["engineering_making", "design", "building_spaces"],
      },
      {
        text: "Knowing someone is better off",
        detail: "Progress you can see in another person",
        tags: ["helping_people", "science_health", "teaching_explaining"],
      },
      {
        text: "Making a measurable improvement",
        detail: "Better results, less waste, or a smarter decision",
        tags: ["data", "money_business", "electricity_energy"],
      },
    ],
  },
  {
    id: "industry",
    theme: "Explore a direction",
    title: "Which real-world challenge would you like to explore?",
    hint: "You don't need experience in any of these. Curiosity is enough.",
    options: [
      {
        text: "Making technology useful and trustworthy",
        detail: "Software, digital design, data, and security",
        tags: ["computers_coding", "security_puzzles", "design"],
      },
      {
        text: "Building greener, better-connected places",
        detail: "Engineering, energy, planning, and infrastructure",
        tags: ["electricity_energy", "building_spaces", "outdoors_maps"],
      },
      {
        text: "Improving health and access to learning",
        detail: "Healthcare, science, and education",
        tags: ["science_health", "teaching_explaining", "helping_people"],
      },
      {
        text: "Understanding how the world makes decisions",
        detail: "Finance, economics, research, and communication",
        tags: ["money_business", "maths", "data", "writing_language"],
      },
    ],
  },
];
export function tagsFromAnswers(answers: Record<string, number>): string[] {
  return [
    ...new Set(questions.flatMap((q) => q.options[answers[q.id]]?.tags ?? [])),
  ];
}
