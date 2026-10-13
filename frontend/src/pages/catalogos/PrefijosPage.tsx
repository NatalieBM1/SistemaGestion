import { CatalogoCRUD } from "../../components/CatalogoCRUD";
import { CATALOGOS } from "../../config/catalogos";

export function PrefijosPage() {
  return <CatalogoCRUD config={CATALOGOS.prefijos} />;
}
