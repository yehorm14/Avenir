// Required source attributions (AGENTS.md section 7). Names and licences follow
// data/manifest.yaml exactly (licences checked 18 Oct); ESCO's page states no licence,
// so only its credit line is shown.
export function Attributions({ adzuna = false }: { adzuna?: boolean }) {
  return (
    <div className="source-attributions">
      <h3>Attribution</h3>
      <ul>
        <li>
          ONS data: contains public sector information licensed under the Open
          Government Licence v3.0.
        </li>
        <li>
          Skills England / DfE Occupations in Demand 2025: contains public
          sector information licensed under the Open Government Licence v3.0.
        </li>
        <li>
          DfE, The impact of AI on UK jobs and training (2023): contains public
          sector information licensed under the Open Government Licence v3.0.
        </li>
        <li>
          Automation exposure adapted from Gmyrek et al., Generative AI and
          Jobs: A Refined Global Index of Occupational Exposure, ILO Working
          Paper 140 (2025), © ILO,{" "}
          <a
            href="https://doi.org/10.54394/HETP0387"
            target="_blank"
            rel="noreferrer"
          >
            doi.org/10.54394/HETP0387
          </a>
          , licensed under CC BY 4.0. Changed by Avenir: scores averaged over
          the ISCO-08 codes each UK occupation maps to. This adaptation has not
          been prepared, reviewed or endorsed by the ILO.
        </li>
        <li>
          National Careers Service job profiles: contains public sector
          information licensed under the Open Government Licence v3.0.
        </li>
        <li>ESCO classification © European Commission.</li>
        <li>
          This product uses the O*NET 31.0 database by the U.S. Department of
          Labor, Employment and Training Administration (USDOL/ETA), under CC BY
          4.0. O*NET is a trademark of USDOL/ETA.
        </li>
        <li>
          Course comparison links go to Discover Uni (HESA); no Discover Uni
          data is reproduced here.
        </li>
        <li>ONS online job advert estimates; underlying adverts: Adzuna.</li>
        {adzuna && (
          <li>
            <a href="https://www.adzuna.co.uk" target="_blank" rel="noreferrer">
              Jobs by Adzuna
            </a>
          </li>
        )}
      </ul>
    </div>
  );
}
