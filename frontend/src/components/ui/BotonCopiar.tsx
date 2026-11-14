import { Copy } from "lucide-react";
import { copiarAlPortapapeles } from "../../lib/portapapeles";
import { IconButton } from "./IconButton";
import { useToast } from "./Toast";
import styles from "./IconButton.module.css";

interface BotonCopiarProps {
  /** Lo que se copia. Si está vacío, el botón no se muestra. */
  texto: string | null | undefined;
  /** Para el lector de pantalla y el tooltip: "Copiar <que>". */
  que: string;
}

/** Botón pequeño (ícono lucide `copy`) que copia `texto` y avisa "Copiado". */
export function BotonCopiar({ texto, que }: BotonCopiarProps) {
  const toast = useToast();
  if (!texto) return null;
  return (
    <IconButton
      label={`Copiar ${que}`}
      icon={<Copy size={14} />}
      className={styles.pequeno}
      onClick={async (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (await copiarAlPortapapeles(texto)) toast.success("Copiado", 1500);
        else toast.error("No se pudo copiar. Selecciona el texto y usa Ctrl+C.");
      }}
    />
  );
}
