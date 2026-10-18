// Required source attributions (AGENTS.md section 7). Names and licences follow
// data/manifest.yaml and snapshots/ml/sources.json exactly; no licence is claimed
// where the manifest still says (verify): Skills England, ILO and ESCO.
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
          Skills England / DfE Occupations in Demand 2025. Licence to be
          confirmed.
        </li>
        <li>
          DfE, The impact of AI on UK jobs and training (2023): contains public
          sector information licensed under the Open Government Licence v3.0.
        </li>
        <li>
          Automation exposure adapted from ILO Working Paper 140 (Gmyrek et al.,
          2025), © ILO 2025. Scores were averaged over the international codes
          a UK occupation maps to; this adaptation was not reviewed or endorsed
          by the ILO.
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
