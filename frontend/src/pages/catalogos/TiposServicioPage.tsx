import { CatalogoCRUD } from "../../components/CatalogoCRUD";
import { CATALOGOS } from "../../config/catalogos";

export function TiposServicioPage() {
  return <CatalogoCRUD config={CATALOGOS.tipos_servicio} />;
}
