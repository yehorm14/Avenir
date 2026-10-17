/**
 * Editorial exploration guides, adapted from Max's Pathfinder pathway structure.
 * Course and organiser links checked against their own websites on 17 October 2026.
 * These are examples, not university rankings, admissions advice or live vacancies.
 * Descriptions and suggested projects are Avenir editorial guidance; labour-market
 * numbers must come from the ML artefacts, never from this file.
 */
export interface UniversityOption {
  name: string;
  course: string;
  url: string;
  nation: string;
}

export interface CareerOpportunity {
  id: string;
  title: string;
  kind: 'Event' | 'Internship' | 'Programme' | 'Community';
  location: string;
  nation: string;
  url: string;
  description: string;
}

export interface CareerContent {
  intro: string;
  dayToDay: string[];
  broadDegree: string;
  whyBroad: string;
  hardSkills: string[];
  softSkills: string[];
  universities: UniversityOption[];
  opportunities: CareerOpportunity[];
  firstSteps: string[];
}

export const contentDisclaimer =
  'Explore these course examples and organisers. Check current dates, entry requirements, costs, accessibility and eligibility on the linked website. These are discovery links, not confirmed openings or rankings.';

const courses = {
  glasgowComputing: { name: 'University of Glasgow', course: 'Computing Science', url: 'https://www.gla.ac.uk/undergraduate/degrees/computingscience/', nation: 'Scotland' },
  edinburghComputing: { name: 'University of Edinburgh', course: 'Computer Science BSc', url: 'https://study.ed.ac.uk/programmes/undergraduate/57-computer-science', nation: 'Scotland' },
  imperialComputing: { name: 'Imperial College London', course: 'Computing BEng', url: 'https://www.imperial.ac.uk/study/courses/undergraduate/computing-beng/', nation: 'England' },
  glasgowMaths: { name: 'University of Glasgow', course: 'Mathematics and Statistics: undergraduate routes', url: 'https://www.gla.ac.uk/schools/mathematicsstatistics/study/undergraduate/', nation: 'Scotland' },
  gsaDesign: { name: 'Glasgow School of Art', course: 'Communication Design BA (Hons)', url: 'https://www.gsa.ac.uk/undergraduate-degrees/communication-design', nation: 'Scotland' },
  ualDesign: { name: 'University of the Arts London', course: 'Graphic Design Communication BA (Hons)', url: 'https://www.arts.ac.uk/subjects/communication-and-graphic-design/undergraduate/ba-hons-graphic-design-communication-chelsea', nation: 'England' },
  edinburghArchitecture: { name: 'University of Edinburgh', course: 'Architecture BA / MA (Hons)', url: 'https://study.ed.ac.uk/programmes/undergraduate/120-architecture', nation: 'Scotland' },
  uclArchitecture: { name: 'UCL', course: 'Architecture BSc', url: 'https://www.ucl.ac.uk/study/prospective-students/undergraduate/courses/architecture-bsc', nation: 'England' },
  napierTechnology: { name: 'Edinburgh Napier University', course: 'Architectural Technology BSc (Hons)', url: 'https://www.napier.ac.uk/courses/bsc-hons-architectural-technology-undergraduate-fulltime', nation: 'Scotland' },
  glasgowCivil: { name: 'University of Glasgow', course: 'Civil Engineering BEng / MEng', url: 'https://www.gla.ac.uk/undergraduate/degrees/civilengineering/', nation: 'Scotland' },
  strathclydeElectrical: { name: 'University of Strathclyde', course: 'Electronic & Electrical Engineering BEng', url: 'https://www.strath.ac.uk/courses/undergraduate/electronicelectricalengineeringbeng/', nation: 'Scotland' },
  collegeEngineering: { name: 'City of Glasgow College', course: 'Mechanical Engineering HNC: course directory', url: 'https://www.cityofglasgowcollege.ac.uk/course-search?search_api_views_fulltext=engineer', nation: 'Scotland' },
  heriotQuantity: { name: 'Heriot-Watt University', course: 'Quantity Surveying BSc (Hons)', url: 'https://www.hw.ac.uk/study/undergraduate/quantity-surveying', nation: 'Scotland' },
  rguBuiltEnvironment: { name: 'Robert Gordon University', course: 'Built Environment Graduate Apprenticeship', url: 'https://www.rgu.ac.uk/study/courses/graduate-apprenticeship-in-bsc-hons-built-environment', nation: 'Scotland' },
  napierSurveying: { name: 'Edinburgh Napier University', course: 'Building Surveying BSc (Hons)', url: 'https://www.napier.ac.uk/courses/bsc-hons-building-surveying-undergraduate-fulltime', nation: 'Scotland' },
  heriotActuarial: { name: 'Heriot-Watt University', course: 'Actuarial Science BSc (Hons)', url: 'https://www.hw.ac.uk/study/undergraduate/actuarial-science', nation: 'Scotland' },
  glasgowEconomics: { name: 'University of Glasgow', course: 'Economics: undergraduate routes', url: 'https://www.gla.ac.uk/undergraduate/degrees/economics/', nation: 'Scotland' },
  lseEconomics: { name: 'London School of Economics', course: 'Economics: undergraduate routes', url: 'https://www.lse.ac.uk/economics/study/undergraduate', nation: 'England' },
  glasgowAccounting: { name: 'University of Glasgow', course: 'Accountancy & Finance BAcc', url: 'https://www.gla.ac.uk/undergraduate/degrees/accountancy/', nation: 'Scotland' },
  gcuImaging: { name: 'Glasgow Caledonian University', course: 'Diagnostic Imaging BSc (Hons)', url: 'https://www.gcu.ac.uk/study/courses/ug/2728/bsc-hons-diagnostic-imaging-glasgow', nation: 'Scotland' },
  cityImaging: { name: "City St George's, University of London", course: 'Diagnostic Radiography BSc (Hons)', url: 'https://www.citystgeorges.ac.uk/prospective-students/courses/undergraduate/radiography-diagnostic-imaging', nation: 'England' },
  strathclydeTeaching: { name: 'University of Strathclyde', course: 'Teaching: subject degrees and PGDE routes', url: 'https://www.strath.ac.uk/studywithus/subjects/teaching/', nation: 'Scotland' },
  edinburghTeaching: { name: 'University of Edinburgh', course: 'PGDE Secondary: postgraduate teacher training', url: 'https://study.ed.ac.uk/programmes/postgraduate-taught/123-professional-graduate-diploma-in-education-secondary', nation: 'Scotland' },
} satisfies Record<string, UniversityOption>;

const opportunities = {
  codebar: { id: 'codebar-london', title: 'codebar London workshops', kind: 'Community', location: 'London', nation: 'England', url: 'https://codebar.io/london', description: 'Explore supportive programming workshops. Read the student guide and eligibility criteria before registering; beginners can start with the linked tutorials.' },
  cyber: { id: 'ncsc-cyber-skills', title: 'NCSC Cyber Skills', kind: 'Programme', location: 'UK-wide / online', nation: 'UK', url: 'https://www.ncsc.gov.uk/cyber-skills', description: 'Find official learning resources and regional partners for cyber pathways. Check the current TechFirst information and age or study-stage requirements.' },
  iet: { id: 'iet-events', title: 'IET engineering talks and communities', kind: 'Event', location: 'UK-wide / online', nation: 'UK', url: 'https://events.theiet.org/search/', description: 'Browse engineering talks, webinars and local networks. Filter for your location and choose an introductory session; audience, fees and booking vary.' },
  ietLondon: { id: 'iet-london', title: 'IET London events', kind: 'Event', location: 'London', nation: 'England', url: 'https://localevents.theiet.org/network/london', description: 'Discover the London engineering community through its official calendar. Check whether each talk welcomes students and people exploring the subject.' },
  ice: { id: 'ice-events', title: 'ICE lectures and site visits', kind: 'Event', location: 'UK-wide / online', nation: 'UK', url: 'https://www.ice.org.uk/events/upcoming-events', description: 'Explore civil engineering lectures, webinars and networking. Search Scotland or London and check prerequisites, access arrangements and any site restrictions.' },
  riba: { id: 'riba-whats-on', title: 'RIBA talks and exhibitions', kind: 'Event', location: 'UK-wide / online', nation: 'UK', url: 'https://www.riba.org/whats-on', description: 'Browse architecture exhibitions, public talks and learning events. Look for public or student sessions; booking requirements and costs vary.' },
  va: { id: 'va-young-people', title: 'V&A creative workshops', kind: 'Event', location: 'London', nation: 'England', url: 'https://www.vam.ac.uk/info/young-people', description: 'Explore design, digital media and architecture activities for young people. Check the age range, accessibility and booking details of the individual activity.' },
  rics: { id: 'rics-scotland', title: 'RICS Scotland and Matrics community', kind: 'Community', location: 'Scotland', nation: 'Scotland', url: 'https://www.rics.org/about-rics/where-we-are/uk-and-ireland/rics-in-scotland', description: 'Discover surveying and the built environment through the regional network. Some activities are for trainees or members; check who can attend before booking.' },
  ricsEvents: { id: 'rics-events', title: 'RICS property and construction events', kind: 'Event', location: 'UK-wide / online', nation: 'UK', url: 'https://www.rics.org/training-events', description: 'Browse the professional body’s training and event directory. Use introductory topics to explore the field; specialist courses may require experience or payment.' },
  rss: { id: 'rss-events', title: 'Royal Statistical Society events', kind: 'Event', location: 'UK-wide / online', nation: 'UK', url: 'https://rss.org.uk/training-events/events/', description: 'Explore statistics talks and local groups, including Scottish and London activities. Check the mathematical level and whether a session is suitable for newcomers.' },
  icaew: { id: 'icaew-careers', title: 'ICAEW career exploration', kind: 'Programme', location: 'UK-wide / online', nation: 'UK', url: 'https://www.icaew.com/start-your-career', description: 'Compare accountancy training routes and discover career resources and employer links. Check each programme’s qualification and application requirements.' },
  springpod: { id: 'springpod-experience', title: 'Springpod virtual work experience', kind: 'Programme', location: 'Online', nation: 'UK', url: 'https://www.springpod.com/virtual-work-experience', description: 'Try a virtual introduction to an industry before committing to it. Browse the current catalogue and check age, registration and programme-specific requirements.' },
  internships: { id: 'bright-network-internships', title: 'Explore internship programmes', kind: 'Internship', location: 'UK-wide / London / online', nation: 'UK', url: 'https://www.brightnetwork.co.uk/internships/?sort_by=deadline', description: 'A discovery directory for students ready to explore internships. Many employers require university enrolment; check the employer’s own listing and current deadline.' },
  scottishApprenticeships: { id: 'scottish-apprenticeships', title: 'Scottish apprenticeship discovery', kind: 'Programme', location: 'Scotland', nation: 'Scotland', url: 'https://www.apprenticeships.scot/', description: 'Compare Foundation, Modern and Graduate Apprenticeship routes and search employers. This is a discovery portal; a place or vacancy is not guaranteed.' },
  sectt: { id: 'sectt-electrical', title: 'SECTT electrical apprenticeship routes', kind: 'Programme', location: 'Scotland', nation: 'Scotland', url: 'https://sectt.org.uk/', description: 'Read the Scottish electrical training route, assessments and employer information. Check the current application process and training requirements directly with SECTT.' },
  nhs: { id: 'nhs-scotland-radiography', title: 'Meet diagnostic radiography', kind: 'Programme', location: 'Scotland / online', nation: 'Scotland', url: 'https://www.careers.nhs.scot/explore-careers/allied-health-professions/diagnostic-radiographer/', description: 'Explore NHS Scotland’s role guide and practitioner stories. Use the official route information to prepare questions for an open day or careers adviser.' },
  teachScotland: { id: 'teach-scotland', title: 'Explore teaching in Scotland', kind: 'Programme', location: 'Scotland / online', nation: 'Scotland', url: 'https://teachinscotland.scot/', description: 'Hear from teachers and compare Scottish routes into secondary teaching. Check subject requirements and professional registration through the official guidance.' },
  teachingEvents: { id: 'get-into-teaching-events', title: 'Teacher training information events', kind: 'Event', location: 'England / online', nation: 'England', url: 'https://getintoteaching.education.gov.uk/events', description: 'Meet training providers and ask about classroom experience and routes into teaching in England. Scottish qualifications and registration follow a different route.' },
} satisfies Record<string, CareerOpportunity>;

const computing: CareerContent = {
  intro: 'Turn a real problem into a reliable digital tool. Software work combines careful reasoning, creative choices and regular conversations with the people using what you build.',
  dayToDay: ['Break a user need into small, testable tasks.', 'Build and test a feature, then investigate why it behaves unexpectedly.', 'Discuss design choices with teammates and improve existing code.'],
  broadDegree: 'Computer Science or Computing Science',
  whyBroad: 'A broad course can build foundations in programming, systems, data and human interaction before you specialise. Compare modules, practical projects and apprenticeship routes rather than choosing by the course title alone.',
  hardSkills: ['Programming and debugging', 'Algorithms and data structures', 'Version control and automated testing', 'Databases and basic system design'],
  softSkills: ['Explaining an idea clearly', 'Working through uncertainty', 'Listening to users', 'Giving and receiving feedback'],
  universities: [courses.glasgowComputing, courses.edinburghComputing, courses.imperialComputing],
  opportunities: [opportunities.codebar, opportunities.springpod, opportunities.scottishApprenticeships],
  firstSteps: ['Build one small tool for a problem you actually have, and ask someone to try it.', 'Keep a short record of what failed, how you debugged it and what you changed.', 'Compare a broad computing degree with a software apprenticeship and speak to a student on each route.'],
};

const design: CareerContent = {
  intro: 'Make information understandable and experiences easier to use. The work is a cycle of observing, making, testing and explaining why a design helps its audience.',
  dayToDay: ['Understand the audience and the purpose of a brief.', 'Explore several ideas through sketches and prototypes.', 'Present your reasoning, gather feedback and refine the result.'],
  broadDegree: 'Communication Design, Interaction Design or a broad design foundation',
  whyBroad: 'A course covering research, visual communication and different media leaves room to explore digital products, branding and editorial work. A thoughtful portfolio can also support college and apprenticeship routes.',
  hardSkills: ['Typography and visual hierarchy', 'Prototyping and layout', 'User research and accessibility', 'Presenting a portfolio with process'],
  softSkills: ['Curiosity about people', 'Constructive critique', 'Explaining trade-offs', 'Collaboration across disciplines'],
  universities: [courses.gsaDesign, courses.ualDesign],
  opportunities: [opportunities.va, opportunities.codebar, opportunities.springpod],
  firstSteps: ['Choose a confusing everyday service and sketch a clearer version.', 'Test the idea with a few people and record what changed after feedback.', 'Build a small portfolio showing your process as well as the finished work.'],
};

const builtEnvironment: CareerContent = {
  intro: 'Shape places around the people who use them. Built-environment work connects design with materials, climate, budgets and the practical constraints of construction.',
  dayToDay: ['Understand a site, a client brief and the needs of its users.', 'Develop drawings or models and check practical constraints.', 'Coordinate with other specialists and explain decisions clearly.'],
  broadDegree: 'Compare Architecture, Architectural Technology and Civil Engineering',
  whyBroad: 'These routes share an interest in buildings but lead to different professional roles. Compare studio design, building technology and engineering content, and check the relevant professional pathway before choosing.',
  hardSkills: ['Technical drawing and digital modelling', 'Materials and construction principles', 'Environmental design', 'Reading plans and checking details'],
  softSkills: ['Spatial reasoning', 'Listening to different viewpoints', 'Communicating visual ideas', 'Balancing practical constraints'],
  universities: [courses.edinburghArchitecture, courses.napierTechnology, courses.uclArchitecture],
  opportunities: [opportunities.riba, opportunities.va, opportunities.ice],
  firstSteps: ['Study a public building and note how light, access and circulation work for different users.', 'Make a simple drawing or model and explain one design decision.', 'Visit a course open day and ask how its route connects to professional qualification.'],
};

const engineering: CareerContent = {
  intro: 'Use science and practical judgement to make systems work safely. Engineering involves calculations, experiments and teamwork as well as designing new things.',
  dayToDay: ['Translate a problem into measurable requirements.', 'Model a possible solution and test its assumptions.', 'Review safety, environmental impact and performance with colleagues.'],
  broadDegree: 'A broad engineering foundation, followed by a discipline that fits',
  whyBroad: 'Look for strong mathematics, design projects and practical work before selecting a narrow application. College and employer-based routes can develop technical skills alongside work; compare the professional progression of each route.',
  hardSkills: ['Applied mathematics and physics', 'Computer-aided design', 'Testing and measurement', 'Technical documentation and safety awareness'],
  softSkills: ['Systematic problem-solving', 'Teamwork', 'Careful observation', 'Explaining evidence and limitations'],
  universities: [courses.glasgowCivil, courses.strathclydeElectrical, courses.collegeEngineering],
  opportunities: [opportunities.iet, opportunities.ice, opportunities.scottishApprenticeships],
  firstSteps: ['Try a safe classroom or simulation project and compare predicted behaviour with the result.', 'Document your design choices, measurements and improvements.', 'Compare a university route with an HNC or apprenticeship, including progression and entry requirements.'],
};

const surveying: CareerContent = {
  intro: 'Help people make sound decisions about buildings and construction. Surveying combines technical knowledge with cost, evidence and clear advice to clients.',
  dayToDay: ['Gather information from drawings, site observations and documents.', 'Assess cost, condition or project risks within your specialism.', 'Write practical recommendations and discuss them with clients and contractors.'],
  broadDegree: 'Surveying or Built Environment, with the right professional specialism',
  whyBroad: 'Quantity surveying, building surveying and property valuation are different jobs. Compare course modules and professional accreditation rather than treating every surveying course as interchangeable. A graduate apprenticeship may combine study and employment.',
  hardSkills: ['Measurement and spreadsheet modelling', 'Understanding construction', 'Reading contracts and technical documents', 'Writing evidence-based reports'],
  softSkills: ['Attention to detail', 'Negotiation', 'Professional judgement', 'Clear client communication'],
  universities: [courses.heriotQuantity, courses.napierSurveying, courses.rguBuiltEnvironment],
  opportunities: [opportunities.rics, opportunities.ricsEvents, opportunities.scottishApprenticeships],
  firstSteps: ['Compare quantity surveying, building surveying and valuation using course examples.', 'Prepare a simple materials budget from a public project or a small model.', 'Ask a surveyor about the balance of site visits, calculations and client work.'],
};

const quantitative: CareerContent = {
  intro: 'Use mathematics and evidence to understand uncertainty. The useful part is not just producing a model: it is knowing what its assumptions allow you to conclude.',
  dayToDay: ['Translate a real question into a measurable problem.', 'Analyse data or model possible outcomes and test assumptions.', 'Explain uncertainty and the limits of your conclusions.'],
  broadDegree: 'Mathematics, Statistics or Economics',
  whyBroad: 'A quantitative foundation can support several sectors before you choose a specialism. Actuarial work has its own professional qualification pathway; a specialised degree may suit you, but compare its modules and exemptions with broader options.',
  hardSkills: ['Probability and statistics', 'Programming or spreadsheet analysis', 'Model checking and data quality', 'Communicating numerical evidence'],
  softSkills: ['Intellectual curiosity', 'Careful reasoning', 'Explaining uncertainty', 'Challenging assumptions respectfully'],
  universities: [courses.glasgowMaths, courses.heriotActuarial, courses.lseEconomics],
  opportunities: [opportunities.rss, opportunities.springpod, opportunities.internships],
  firstSteps: ['Choose a public dataset and answer one clear question with a chart and a written explanation.', 'List what your data cannot tell you and one assumption that could change the answer.', 'Compare mathematics, statistics, economics and actuarial course modules before narrowing your choice.'],
};

const finance: CareerContent = {
  intro: 'Help an organisation understand its financial position and make considered decisions. Good financial work combines numerical care with scepticism, ethics and clear explanations.',
  dayToDay: ['Read financial information and check the underlying evidence.', 'Compare alternatives, risks and the assumptions behind them.', 'Present a clear recommendation and explain what could change it.'],
  broadDegree: 'Accounting and Finance, Economics, Mathematics or Business',
  whyBroad: 'Finance has several entry routes. Compare a degree with a school-leaver or apprenticeship route and the professional training involved. A broad analytical course can leave room for accounting, analysis and other business roles.',
  hardSkills: ['Financial statements and cash flow', 'Spreadsheet analysis', 'Research and data checking', 'Writing a reasoned financial explanation'],
  softSkills: ['Integrity', 'Attention to detail', 'Explaining trade-offs', 'Working constructively under deadlines'],
  universities: [courses.glasgowAccounting, courses.glasgowEconomics, courses.lseEconomics],
  opportunities: [opportunities.icaew, opportunities.springpod, opportunities.internships],
  firstSteps: ['Read an organisation’s published annual report and explain how it makes and spends money.', 'Build a simple budget with explicit assumptions and check it for errors.', 'Compare graduate, school-leaver and apprenticeship routes, including any professional exams.'],
};

const teaching: CareerContent = {
  intro: 'Help young people understand a subject and grow in confidence. Teaching combines deep subject knowledge with explanation, planning and adapting to different needs.',
  dayToDay: ['Plan lessons and explain an idea in more than one way.', 'Check understanding and give useful feedback.', 'Work with colleagues and families to support pupils.'],
  broadDegree: 'A subject you enjoy teaching, followed by the appropriate teacher training',
  whyBroad: 'A strong subject degree can keep options open while you test whether classroom work suits you. Teacher training and registration differ between UK nations; an Education degree alone does not automatically qualify you to teach.',
  hardSkills: ['Subject knowledge', 'Lesson planning and assessment', 'Accessible explanation', 'Digital teaching resources'],
  softSkills: ['Patience', 'Empathy and boundaries', 'Public speaking', 'Reflecting on feedback'],
  universities: [courses.strathclydeTeaching, courses.edinburghTeaching],
  opportunities: [opportunities.teachScotland, opportunities.teachingEvents, opportunities.springpod],
  firstSteps: ['Explain a difficult idea to someone and ask what helped them understand it.', 'Ask your school about supervised opportunities to support younger pupils.', 'Compare the entry requirements for your chosen teaching subject in Scotland and any other nation you are considering.'],
};

/** One entry for every SOC in Arsenii's committed 20-career demo set. */
export const careerContent: Record<string, CareerContent> = {
  '2134': computing,
  '3544': {
    ...quantitative,
    intro: 'Turn messy information into a useful answer. Data analysts connect numbers with the decisions a team is trying to make, and check that the evidence supports the story.',
    dayToDay: ['Clarify a question with the people making a decision.', 'Clean, join and analyse data, checking for gaps and misleading patterns.', 'Build a clear chart or dashboard and explain the implications.'],
    broadDegree: 'Statistics, Mathematics, Computer Science or Economics',
    hardSkills: ['SQL and spreadsheets', 'Python or R', 'Data visualisation', 'Statistics and data quality checks'],
    universities: [courses.glasgowMaths, courses.edinburghComputing, courses.lseEconomics],
  },
  '2133': {
    ...computing,
    intro: 'Connect an organisation’s needs with systems that actually help. This path suits someone who enjoys understanding people, mapping complicated processes and turning ambiguity into a workable plan.',
    dayToDay: ['Interview users and map how a process works today.', 'Turn business needs into requirements and possible system designs.', 'Test proposed changes with technical teams and the people affected.'],
    broadDegree: 'Computing Science, Information Systems or Computing with Business',
    hardSkills: ['Requirements gathering', 'Process and system modelling', 'SQL and data interpretation', 'Writing testable acceptance criteria'],
    softSkills: ['Active listening', 'Asking precise questions', 'Facilitating agreement', 'Explaining technical choices plainly'],
    firstSteps: ['Map a process at school or in a club and identify one avoidable problem.', 'Write a short specification for an improvement, including who benefits and how to test it.', 'Compare computing courses with business or information-systems options.'],
  },
  '2135': {
    ...computing,
    intro: 'Help people and organisations understand and reduce digital risks. Cyber security includes systems, investigations, policy and communication; curiosity and responsible judgement matter alongside technical skill.',
    dayToDay: ['Investigate suspicious activity and assess what evidence means.', 'Find weaknesses in systems with clear permission and a defined scope.', 'Help teams improve protection and explain risks in practical terms.'],
    whyBroad: 'Computer Science can give you programming, networks and systems foundations while leaving software and data routes open. A specialised cyber course is another option: compare its practical content, professional recognition and flexibility rather than assuming one title is always better.',
    hardSkills: ['Networks and operating systems', 'Secure programming', 'Log analysis and incident investigation', 'Risk assessment and clear reporting'],
    opportunities: [opportunities.cyber, opportunities.codebar, opportunities.scottishApprenticeships],
    firstSteps: ['Learn basic networking and practise only in a legal, purpose-built training environment.', 'Write a short guide that helps a club protect accounts and recognise phishing.', 'Compare a broad computing course with a cyber course and ask how students can change specialism.'],
  },
  '2141': {
    ...design,
    intro: 'Design websites around what people need to do. Web design joins visual judgement with accessibility, research and enough technical understanding to make an idea work on real screens.',
    dayToDay: ['Map a user journey and sketch a page structure.', 'Prototype a responsive interface and test its accessibility.', 'Work with developers and refine the design after feedback.'],
    hardSkills: ['Responsive layout and typography', 'HTML and CSS foundations', 'Interface prototyping', 'Usability testing and accessibility'],
  },
  '2142': {
    ...design,
    intro: 'Communicate ideas through images, type, motion and digital media. A strong designer makes choices for an audience and can show how the work developed from the brief.',
    dayToDay: ['Research a brief and develop several visual directions.', 'Create layouts, imagery or motion work across different formats.', 'Refine a design with feedback and prepare final files carefully.'],
    hardSkills: ['Typography and composition', 'Image-making and editing', 'Motion or digital media fundamentals', 'Portfolio development and production workflows'],
    opportunities: [opportunities.va, opportunities.springpod],
  },
  '2451': {
    ...builtEnvironment,
    intro: 'Bring creative ideas and technical constraints together to shape buildings. Architecture involves understanding people and places, developing proposals and coordinating with specialists over a long project.',
    broadDegree: 'Architecture, compared carefully with other built-environment routes',
    whyBroad: 'Architecture, architectural technology and engineering offer different balances of design and technical work. Architecture also has a professional qualification route that is changing: use the current course and regulator guidance rather than assuming a first degree alone qualifies you.',
    universities: [courses.edinburghArchitecture, courses.uclArchitecture],
  },
  '2452': {
    ...builtEnvironment,
    intro: 'Make buildings and places work in practice. This occupation group includes architectural technology and planning: technology focuses on how buildings are delivered, while planning considers how places develop.',
    dayToDay: ['For technology: develop detailed building information and coordinate design requirements.', 'For planning: research a place and evaluate proposals against community and policy needs.', 'Explain evidence and practical constraints to other people on a project.'],
    broadDegree: 'Architectural Technology, or Planning if policy and places interest you more',
    whyBroad: 'These are related but distinct specialisms. The course examples below focus on architectural technology; if planning is your goal, compare dedicated planning courses and their professional recognition before applying.',
    universities: [courses.napierTechnology, courses.edinburghArchitecture],
    hardSkills: ['Building information modelling', 'Construction detailing', 'Researching site and planning constraints', 'Technical documentation'],
  },
  '3120': {
    ...builtEnvironment,
    intro: 'Turn design ideas into accurate drawings and models that other people can build from. Technical detail, digital tools and coordination are central to CAD and architectural technician work.',
    dayToDay: ['Create and update drawings or building models.', 'Check dimensions, materials and consistency between documents.', 'Coordinate changes with designers, engineers and construction teams.'],
    broadDegree: 'Architectural Technology, an HNC/HND or an employer-based technical route',
    whyBroad: 'A practical college or apprenticeship route may suit this work as well as a degree. Compare drawing, modelling and construction content, then check how the qualification supports progression into your chosen technical role.',
    universities: [courses.napierTechnology, courses.collegeEngineering],
    hardSkills: ['CAD and building information modelling', 'Dimensioning and technical drawing', 'Construction and materials knowledge', 'Document control and accuracy checks'],
    opportunities: [opportunities.riba, opportunities.scottishApprenticeships, opportunities.springpod],
  },
  '2121': {
    ...engineering,
    intro: 'Design and improve the infrastructure people rely on: buildings, transport, water and the systems connecting them. Civil engineering joins technical analysis with responsibility to communities and the environment.',
    dayToDay: ['Analyse loads, ground conditions or water and transport systems.', 'Develop designs and test their safety and environmental assumptions.', 'Coordinate drawings, site information and decisions with a project team.'],
    broadDegree: 'Civil Engineering',
    whyBroad: 'A broad civil engineering course can introduce structures, water, transport and ground engineering before specialisation. Compare practical projects, placements and accreditation with a civil engineering apprenticeship route.',
    universities: [courses.glasgowCivil],
    hardSkills: ['Mechanics and applied mathematics', 'Structural or environmental modelling', 'CAD and engineering drawings', 'Site data, materials and safety principles'],
    opportunities: [opportunities.ice, opportunities.iet, opportunities.scottishApprenticeships],
  },
  '2123': {
    ...engineering,
    intro: 'Work with the electrical and electronic systems behind energy, communication and everyday technology. The field offers room to explore power, control, electronics and embedded software.',
    dayToDay: ['Model a circuit, power system or control problem.', 'Test a design and investigate unexpected measurements.', 'Document reliability and safety decisions with a wider engineering team.'],
    broadDegree: 'Electronic and Electrical Engineering',
    whyBroad: 'A course covering circuits, power, control and computing can leave several specialisms open. Compare that breadth with practical training routes and ask how each path supports professional progression.',
    universities: [courses.strathclydeElectrical],
    hardSkills: ['Circuit analysis', 'Electronics and measurement', 'Control systems or embedded programming', 'Technical modelling and documentation'],
    opportunities: [opportunities.iet, opportunities.ietLondon, opportunities.scottishApprenticeships],
    firstSteps: ['Use a circuit simulator to test a simple low-voltage design before any supervised practical work.', 'Explain how changing one component changes the result.', 'Compare an electronic and electrical engineering course with a technical apprenticeship; ask about power, robotics and communication options.'],
  },
  '3113': {
    ...engineering,
    intro: 'Make engineering ideas work on the ground. Technicians build, measure, test and maintain equipment, using practical judgement and accurate records to help a team solve real problems.',
    dayToDay: ['Set up equipment or prepare a test to a specification.', 'Take measurements and investigate faults methodically.', 'Record findings and work with engineers to improve performance.'],
    broadDegree: 'An engineering HNC/HND, apprenticeship or relevant engineering degree',
    whyBroad: 'Hands-on training and supervised workplace experience can be especially valuable. Choose a route matching the systems you enjoy, and compare its progression options rather than treating university as the only starting point.',
    universities: [courses.collegeEngineering, courses.strathclydeElectrical],
    hardSkills: ['Measurement and calibration', 'Reading technical drawings', 'Fault finding', 'Safe workshop practice and documentation'],
  },
  '2453': {
    ...surveying,
    intro: 'Help a construction project use its budget well. Quantity surveyors track costs, contracts and change, balancing value with the practical realities of delivering a building or infrastructure project.',
    dayToDay: ['Measure work and prepare or check cost estimates.', 'Monitor project spending and assess the effect of changes.', 'Discuss contracts, payments and risks with clients and contractors.'],
    broadDegree: 'Quantity Surveying or a relevant Built Environment apprenticeship',
    universities: [courses.heriotQuantity, courses.rguBuiltEnvironment],
    hardSkills: ['Cost planning and measurement', 'Spreadsheet modelling', 'Construction contracts', 'Procurement and project records'],
  },
  '2454': {
    ...surveying,
    intro: 'Investigate buildings and property so people can make informed decisions. Chartered surveying includes several specialisms, so the right course depends on whether you prefer building condition, land, valuation or another area.',
    dayToDay: ['Inspect a property or review reliable information about it.', 'Assess condition, value or suitability within your specialism.', 'Write a clear report explaining findings, limits and next actions.'],
    broadDegree: 'Building Surveying or the surveying specialism you want to explore',
    whyBroad: 'Surveying is a professional family rather than a single interchangeable route. The examples here emphasise building surveying; compare the relevant accredited course and professional training for your intended specialism.',
    universities: [courses.napierSurveying, courses.rguBuiltEnvironment],
  },
  '2433': {
    ...quantitative,
    intro: 'This group brings together actuaries, economists and statisticians. They share quantitative reasoning but ask different questions: risk and uncertainty, economic choices, or what data can reliably show.',
    dayToDay: ['Choose a question and a suitable mathematical or economic model.', 'Check data quality, assumptions and sensitivity to change.', 'Explain the findings and uncertainty to people making decisions.'],
  },
  '2422': {
    ...finance,
    intro: 'Investigate organisations, markets or investments and explain the evidence behind a decision. This path can involve deep research, quantitative analysis and careful communication about uncertainty.',
    dayToDay: ['Research an organisation, sector or economic question.', 'Compare financial scenarios and test the assumptions in a model.', 'Present a reasoned view, including risks and evidence that could change it.'],
    hardSkills: ['Financial modelling', 'Interpreting accounts and economic data', 'Research and source checking', 'Presenting risk and uncertainty'],
    opportunities: [opportunities.springpod, opportunities.internships, opportunities.rss],
  },
  '2421': {
    ...finance,
    intro: 'Help organisations keep reliable financial records and understand what those records mean. Accountancy can lead into reporting, audit, tax, management accounting and broader business decisions.',
    dayToDay: ['Prepare or check financial records and reconcile differences.', 'Investigate an issue and document the evidence behind a judgement.', 'Explain financial information and deadlines to clients or colleagues.'],
    hardSkills: ['Bookkeeping and financial reporting', 'Spreadsheet checks and reconciliation', 'Understanding controls and audit evidence', 'Applying professional standards'],
    universities: [courses.glasgowAccounting, courses.glasgowEconomics],
  },
  '2254': {
    intro: 'Combine healthcare, technology and patient care. Medical radiography includes diagnostic imaging and therapeutic work; the course examples here focus on diagnostic imaging, so compare the two before choosing.',
    dayToDay: ['Explain an imaging procedure and support a patient who may be anxious or in pain.', 'Position and operate equipment safely within your training and role.', 'Check image quality and work with a wider clinical team.'],
    broadDegree: 'An approved Diagnostic Radiography or Diagnostic Imaging programme',
    whyBroad: 'This is a professional healthcare route with specific clinical training and registration requirements. A broad science degree is not a direct substitute. If treatment delivery interests you more, explore therapeutic radiography separately.',
    hardSkills: ['Anatomy and imaging science', 'Image quality and equipment knowledge', 'Clinical safety and accurate records', 'Patient positioning and supervised clinical practice'],
    softSkills: ['Empathy', 'Clear communication', 'Composure', 'Teamwork and professional responsibility'],
    universities: [courses.gcuImaging, courses.cityImaging],
    opportunities: [opportunities.nhs, opportunities.springpod],
    firstSteps: ['Explore the difference between diagnostic and therapeutic radiography through official NHS guidance.', 'Prepare questions about clinical placements, patient contact and shift patterns for a university open day.', 'Ask a school careers adviser about appropriate, supervised healthcare insight opportunities.'],
  },
  '5241': {
    intro: 'Install, test and maintain electrical systems that people depend on. This is practical work with a strong safety culture: reliable judgement, methodical testing and clear communication matter every day.',
    dayToDay: ['Read plans and prepare work within the agreed safety procedures.', 'Install or maintain systems under the right supervision and authorisation.', 'Test, document and explain work carefully.'],
    broadDegree: 'A recognised electrical installation apprenticeship and college training',
    whyBroad: 'A university degree is not the usual starting point for electrical installation. Compare the recognised training route in your nation and how workplace learning, college study and assessment fit together. Electrical engineering is a related but different career.',
    hardSkills: ['Electrical principles', 'Reading plans and diagrams', 'Inspection and testing', 'Safe working procedures and record keeping'],
    softSkills: ['Practical problem-solving', 'Attention to detail', 'Reliability', 'Explaining work to customers'],
    universities: [],
    opportunities: [opportunities.sectt, opportunities.scottishApprenticeships, opportunities.iet],
    firstSteps: ['Read the recognised apprenticeship route for the nation where you plan to train.', 'Ask a training provider about assessment, employer sponsorship and college attendance.', 'Explore basic electrical ideas through a simulator or supervised classroom activity; practical installation work needs proper training and supervision.'],
  },
  '2313': teaching,
};

const families: Record<string, CareerContent> = {
  software: computing, computing, technology: computing, digital: computing,
  design, creative: design, architecture: builtEnvironment, built_environment: builtEnvironment,
  engineering, surveying, construction: surveying, finance, accounting: finance,
  quantitative, data: quantitative, education: teaching, teaching,
};

const fallback: CareerContent = {
  intro: 'Explore what the work involves, test your interest with a small project and compare the routes before making a commitment.',
  dayToDay: ['Research what practitioners actually do.', 'Try a small, relevant task and reflect on the experience.', 'Discuss the route with a student, practitioner or careers adviser.'],
  broadDegree: 'Compare broad study, college and apprenticeship routes',
  whyBroad: 'A course title alone does not show its flexibility. Compare modules, practical work, entry requirements and professional recognition against several careers that interest you.',
  hardSkills: ['Researching reliable sources', 'Building a relevant project', 'Documenting evidence'],
  softSkills: ['Curiosity', 'Communication', 'Reflecting on feedback'],
  universities: [],
  opportunities: [opportunities.springpod, opportunities.scottishApprenticeships],
  firstSteps: ['Write down what attracts you to the role and one thing you want to test.', 'Try a small project and record which parts you enjoyed.', 'Speak with a careers adviser about study and work-based routes.'],
};

export function getCareerContent(soc: string, family?: string): CareerContent {
  return careerContent[soc] ?? families[(family ?? '').toLowerCase().replace(/[ -]+/g, '_')] ?? fallback;
}

/** Direct primary-source references for the directory; checked 17 October 2026. */
export const sourceLinks = [
  ...Object.values(courses).map(({ name, course, url }) => ({ title: `${name}: ${course}`, url })),
  ...Object.values(opportunities).map(({ title, url }) => ({ title, url })),
];
