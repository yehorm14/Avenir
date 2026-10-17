from .base import SourceAdapter, SourceInfo


class SkillsEnglandAdapter(SourceAdapter):
    info = SourceInfo(
        id="skills_england",
        name="Skills England annual skills report 2026 and sector assessments",
        publisher="Skills England",
        url="https://www.gov.uk/government/organisations/skills-england",
        licence="Open Government Licence v3.0",
        gives="Priority occupations and projected employment growth to 2035",
        coverage="England (projections used as the UK-wide signal)",
    )
    snapshot_file = "skills_england.json"


class EmployerSkillsSurveyAdapter(SourceAdapter):
    info = SourceInfo(
        id="ess",
        name="Employer Skills Survey 2024 (and 2022 for the change feed)",
        publisher="Department for Education",
        url="https://explore-education-statistics.service.gov.uk/find-statistics/employer-skills-survey",
        licence="Open Government Licence v3.0",
        gives="Skill-shortage vacancies by occupation",
        coverage="UK",
    )
    snapshot_file = "ess.json"


class OnetAdapter(SourceAdapter):
    info = SourceInfo(
        id="onet",
        name="O*NET database (Interests) and Interest Profiler",
        publisher="O*NET Resource Center, US Department of Labor",
        url="https://www.onetcenter.org/database.html",
        licence="CC BY 4.0",
        gives="Interest (RIASEC) profile per occupation, interest quiz",
        coverage="US occupations, mapped to UK SOC 2020",
    )
    snapshot_file = "onet.json"


class DiscoverUniAdapter(SourceAdapter):
    info = SourceInfo(
        id="discover_uni",
        name="Discover Uni dataset",
        publisher="Jisc (HESA) for the UK funding and regulatory bodies",
        url="https://discoveruni.gov.uk/",
        licence="CC BY 4.0",
        gives="University courses and graduate earnings",
        coverage="UK",
    )
    snapshot_file = "discover_uni.json"


class OccupationalMapsAdapter(SourceAdapter):
    info = SourceInfo(
        id="occupational_maps",
        name="Skills England occupational maps",
        publisher="Skills England",
        url="https://occupational-maps.skillsengland.education.gov.uk/",
        licence="Open Government Licence v3.0",
        gives="Apprenticeships, T Levels and skills per occupation",
        coverage="England only",
    )
    snapshot_file = "occupational_maps.json"


class TemporaryShortageListAdapter(SourceAdapter):
    info = SourceInfo(
        id="tsl",
        name="Temporary Shortage List",
        publisher="Home Office",
        url="https://www.gov.uk/government/publications/skilled-worker-visa-temporary-shortage-list",
        licence="Open Government Licence v3.0",
        gives="Context only, not scored",
        coverage="UK",
        scored=False,
    )


class RegionalSkillsAssessmentAdapter(SourceAdapter):
    info = SourceInfo(
        id="sds_rsa",
        name="Regional Skills Assessments",
        publisher="Skills Development Scotland",
        url="https://www.skillsdevelopmentscotland.co.uk/what-we-do/our-research-evidence/regional-skills-assessments",
        licence="See publisher",
        gives="Context only, not scored",
        coverage="Scotland",
        scored=False,
    )


class AsheAdapter(SourceAdapter):
    info = SourceInfo(
        id="ashe",
        name="Annual Survey of Hours and Earnings (ASHE)",
        publisher="Office for National Statistics",
        url="https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours",
        licence="Open Government Licence v3.0",
        gives="Pay by occupation: median and spread",
        coverage="UK",
    )
    snapshot_file = "ashe.json"


class AiExposureAdapter(SourceAdapter):
    info = SourceInfo(
        id="ai_exposure",
        name="Generative AI and jobs: refined global index (ILO Working Paper 140, 2025)",
        publisher="International Labour Organization",
        url="https://www.ilo.org/node/706766",
        licence="CC BY 4.0",
        gives="Task-level exposure to generative AI",
        coverage="Global, ISCO-08 mapped to SOC 2020",
    )
    snapshot_file = "ai_exposure.json"


class RegionsAdapter(SourceAdapter):
    info = SourceInfo(
        id="regions",
        name="Occupations in Demand 2025 and regional skills assessments",
        publisher="Department for Education; Skills Development Scotland; Welsh and NI regional partnerships",
        url="https://explore-education-statistics.service.gov.uk/methodology/occupations-in-demand-2025-methodology",
        licence="Open Government Licence v3.0",
        gives="Regional lens: demand by sector for each nation and English region",
        coverage="UK nations and English regions",
    )
    snapshot_file = "regions.json"


class NationsAdapter(SourceAdapter):
    info = SourceInfo(
        id="nations",
        name="Apprenticeship routes outside England",
        publisher="Skills Development Scotland (apprenticeships.scot); Apprenticeships Wales; ApprenticeshipsNI",
        url="https://www.apprenticeships.scot/",
        licence="See publishers",
        gives="Modern, Foundation and Graduate Apprenticeships; Welsh and NI routes",
        coverage="Scotland, Wales, Northern Ireland",
    )
    snapshot_file = "nations.json"


class BacktestAdapter(SourceAdapter):
    info = SourceInfo(
        id="backtest",
        name="Self-grade series: past signals and what happened next",
        publisher="Pathfinder team (built from ESS, Working Futures, LFS and ASHE)",
        url=None,
        licence="Open",
        gives="Proof: past demand signals against employment and pay 4 years later",
        coverage="UK",
        scored=False,
    )
    snapshot_file = "backtest.json"


class LightcastAdapter(SourceAdapter):
    info = SourceInfo(
        id="lightcast",
        name="Job-advert data coded to SOC 2020",
        publisher="Lightcast (commercial)",
        url="https://lightcast.io/resources/blog/lightcast-latest-uk-datarun-includes-move-to-soc-2020",
        licence="Commercial licence required: not connected",
        gives="Weekly regional demand (planned, not scored until licensed)",
        coverage="UK",
        scored=False,
    )


class OpportunitiesAdapter(SourceAdapter):
    info = SourceInfo(
        id="opportunities",
        name="Opportunities: programmes, open days, hackathons, competitions and communities",
        publisher="Organisers' own sites (curated by the Pathfinder team)",
        url=None,
        licence="Links only: organisers' terms apply",
        gives="Opportunities by field, stage and nation, with typical timing",
        coverage="UK",
        scored=False,
    )
    snapshot_file = "opportunities.json"


class LiveFeedsAdapter(SourceAdapter):
    info = SourceInfo(
        id="opportunity_feeds",
        name="Employer careers pages and event listings (planned live feeds)",
        publisher="Employers, event platforms and universities",
        url=None,
        licence="Per source: not connected",
        gives="Dated opportunities (open days, hackathons, internships) refreshed daily",
        coverage="UK",
        scored=False,
    )


class CpiAdapter(SourceAdapter):
    info = SourceInfo(
        id="cpi",
        name="Consumer Prices Index (CPI), annual averages",
        publisher="Office for National Statistics",
        url="https://www.ons.gov.uk/economy/inflationandpriceindices",
        licence="Open Government Licence v3.0",
        gives="Inflation, used to put pay from different years in today's money",
        coverage="UK",
        scored=False,
    )
    snapshot_file = "cpi.json"


class AsheSeriesAdapter(SourceAdapter):
    info = SourceInfo(
        id="ashe_series",
        name="ASHE pay history by occupation (median and middle half)",
        publisher="Office for National Statistics",
        url="https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours",
        licence="Open Government Licence v3.0",
        gives="Pay each year, 2015 to 2025, and its spread: SYNTHETIC in this build",
        coverage="UK",
        scored=False,
    )
    snapshot_file = "ashe_series.json"


ADAPTERS: list[SourceAdapter] = [
    SkillsEnglandAdapter(),
    EmployerSkillsSurveyAdapter(),
    OnetAdapter(),
    DiscoverUniAdapter(),
    OccupationalMapsAdapter(),
    AsheAdapter(),
    AiExposureAdapter(),
    RegionsAdapter(),
    NationsAdapter(),
    BacktestAdapter(),
    LightcastAdapter(),
    CpiAdapter(),
    AsheSeriesAdapter(),
    OpportunitiesAdapter(),
    LiveFeedsAdapter(),
    TemporaryShortageListAdapter(),
]

__all__ = ["ADAPTERS", "SourceAdapter", "SourceInfo"]
