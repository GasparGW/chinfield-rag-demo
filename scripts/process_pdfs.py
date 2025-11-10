"""
Script de Procesamiento de PDFs - Chinfield
Convierte fichas técnicas PDF en archivos .txt estructurados para ChromaDB
"""

import os
import re
from pathlib import Path
from typing import Dict, List
import PyPDF2


class ChinfieldPDFProcessor:
    """Procesador de fichas técnicas Chinfield"""
    
    def __init__(self, pdf_dir: str, output_dir: str):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extraer texto completo de un PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"  ❌ Error leyendo {pdf_path.name}: {e}")
            return ""
    
    def parse_ficha_tecnica(self, text: str, filename: str) -> Dict[str, str]:
        """
        Parsear texto de ficha técnica y extraer campos estructurados
        Versión mejorada que maneja variaciones de formato
        """
        # Normalizar espacios pero mantener saltos de línea importantes
        text = re.sub(r'\s+', ' ', text)
        
        # Lista de secciones comunes que pueden terminar un campo
        section_headers = [
            'FÓRMULA', 'ESPECIE DE DESTINO', 'INDICACIONES', 'PRESENTACIÓN',
            'POSOLOGÍA', 'DOSIS', 'VÍAS DE ADMINISTRACIÓN', 'CONTRAINDICACIONES',
            'EFECTOS', 'ADVERTENCIAS', 'CONSERVACIÓN', 'APARIENCIA',
            'PRECAUCIONES', 'INTERACCIONES', 'TIEMPO DE RETIRO'
        ]
        
        # Crear pattern para cualquier header de sección
        next_section = '|'.join([f'(?:{h})' for h in section_headers])
        
        # Extraer nombre del producto
        nombre_patterns = [
            r'Nombre del producto:\s*(.+?)(?:FÓRMULA|Cada|$)',
            r'FICHA TÉCNICA\s+(.+?)(?:FÓRMULA|Cada|$)',
        ]
        nombre = filename.replace('.pdf', '')
        for pattern in nombre_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                nombre = match.group(1).strip()
                # Limpiar nombre (quitar "Nombre del producto:")
                nombre = re.sub(r'^Nombre del producto:\s*', '', nombre, flags=re.IGNORECASE)
                break
        
        # Extraer fórmula - capturar hasta la siguiente sección
        formula_match = re.search(
            rf'FÓRMULA:(.+?)(?:{next_section}|Página|$)', 
            text, re.IGNORECASE | re.DOTALL
        )
        formula = formula_match.group(1).strip() if formula_match else "No especificada"
        
        # Extraer especie de destino
        especie_match = re.search(
            rf'ESPECIE DE DESTINO:(.+?)(?:{next_section}|Página|$)', 
            text, re.IGNORECASE | re.DOTALL
        )
        especie = especie_match.group(1).strip() if especie_match else "No especificada"
        
        # Extraer indicaciones - más flexible
        indicaciones_patterns = [
            rf'INDICACIONES:(.+?)(?:{next_section}|Página|$)',
            rf'I\s*N\s*D\s*I\s*C\s*A\s*C\s*I\s*O\s*N\s*E\s*S:(.+?)(?:{next_section}|Página|$)',
        ]
        indicaciones = "No especificadas"
        for pattern in indicaciones_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                indicaciones = match.group(1).strip()
                break
        
        # Extraer posología - múltiples variantes
        posologia_patterns = [
            rf'POSOLOGÍA.*?:(.+?)(?:{next_section}|Página|$)',
            rf'DOSIS.*?:(.+?)(?:{next_section}|Página|$)',
            rf'POSOLOGÍA Y DOSIS.*?:(.+?)(?:{next_section}|Página|$)',
            rf'VÍAS DE ADMINISTRACIÓN:(.+?)(?:{next_section}|Página|$)',
        ]
        posologia = "No especificada"
        for pattern in posologia_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 10:  # Validar que tenga contenido real
                    posologia = content
                    break
        
        # Extraer contraindicaciones
        contra_match = re.search(
            rf'CONTRAINDICACIONES:(.+?)(?:{next_section}|Página|$)', 
            text, re.IGNORECASE | re.DOTALL
        )
        contraindicaciones = contra_match.group(1).strip() if contra_match else "No especificadas"
        
        # Extraer presentación
        presentacion_patterns = [
            rf'PRESENTACIÓN:(.+?)(?:{next_section}|Página|$)',
            rf'PR\s*E\s*S\s*E\s*N\s*T\s*A\s*C\s*I\s*ÓN:(.+?)(?:{next_section}|Página|$)',
        ]
        presentacion = "No especificada"
        for pattern in presentacion_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                presentacion = match.group(1).strip()
                break
        
        # Limpiar textos capturados (quitar exceso de espacios, headers residuales)
        def clean_text(t):
            # Quitar múltiples espacios
            t = re.sub(r'\s+', ' ', t)
            # Quitar referencias a páginas
            t = re.sub(r'Página\s+\d+\s+de\s+\d+', '', t, flags=re.IGNORECASE)
            # Quitar info de contacto repetida
            t = re.sub(r'LABORATORIO DE ESPECIALIDADES VETERINARIAS.+?(?=\w|$)', '', t, flags=re.IGNORECASE | re.DOTALL)
            t = re.sub(r'E-mail:\s*info@chinfield\.com.+?(?=\w|$)', '', t, flags=re.IGNORECASE)
            return t.strip()
        
        return {
            'nombre': clean_text(nombre),
            'formula': clean_text(formula),
            'especie': clean_text(especie),
            'indicaciones': clean_text(indicaciones),
            'posologia': clean_text(posologia),
            'contraindicaciones': clean_text(contraindicaciones),
            'presentacion': clean_text(presentacion)
        }
    
    def generate_txt_file(self, data: Dict[str, str], output_path: Path):
        """Generar archivo .txt estructurado"""
        
        content = f"""PRODUCTO: {data['nombre']}

=== FÓRMULA ===
{data['formula']}

=== ESPECIE DE DESTINO ===
{data['especie']}

=== INDICACIONES ===
{data['indicaciones']}

=== POSOLOGÍA Y DOSIS ===
{data['posologia']}

=== CONTRAINDICACIONES ===
{data['contraindicaciones']}

=== PRESENTACIÓN ===
{data['presentacion']}

---
Fuente: Laboratorio Chinfield S.A.
Ficha técnica oficial del producto.
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
    
    def process_all_pdfs(self) -> List[str]:
        """Procesar todos los PDFs en el directorio"""
        
        print(f"🔍 Buscando PDFs en: {self.pdf_dir}")
        pdf_files = sorted(self.pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"❌ No se encontraron PDFs en {self.pdf_dir}")
            return []
        
        print(f"📄 Encontrados {len(pdf_files)} PDFs\n")
        
        processed = []
        failed = []
        
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Procesando: {pdf_path.name}")
            
            # Extraer texto
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text or len(text) < 100:
                print(f"  ⚠️  Texto insuficiente, saltando...")
                failed.append(pdf_path.name)
                continue
            
            # Parsear datos
            data = self.parse_ficha_tecnica(text, pdf_path.stem)
            
            # Generar nombre de archivo .txt limpio
            # Reemplazar espacios y caracteres especiales
            safe_name = re.sub(r'[^\w\s-]', '', data['nombre'])
            safe_name = re.sub(r'[-\s]+', '_', safe_name)
            txt_filename = f"producto_{i:02d}_{safe_name[:50]}.txt"
            
            output_path = self.output_dir / txt_filename
            
            # Guardar archivo
            self.generate_txt_file(data, output_path)
            print(f"  ✅ Generado: {txt_filename}")
            
            processed.append(txt_filename)
        
        # Resumen
        print("\n" + "="*70)
        print(f"✅ PROCESAMIENTO COMPLETADO")
        print("="*70)
        print(f"Total PDFs procesados: {len(processed)}/{len(pdf_files)}")
        print(f"Archivos .txt generados: {len(processed)}")
        print(f"Errores: {len(failed)}")
        
        if failed:
            print(f"\n⚠️  PDFs con errores:")
            for f in failed:
                print(f"  - {f}")
        
        print(f"\n📁 Archivos guardados en: {self.output_dir}")
        
        return processed


def main():
    """Función principal"""
    
    print("="*70)
    print("🚀 PROCESADOR DE PDFs - LABORATORIO CHINFIELD")
    print("="*70)
    print()
    
    # Configuración de rutas (desde donde se ejecuta el script)
    BASE_DIR = Path.cwd()  # Directorio actual de ejecución
    PDF_DIR = BASE_DIR / "data" / "productos_pdf"
    OUTPUT_DIR = BASE_DIR / "data" / "products"
    
    print(f"📂 Directorio PDFs: {PDF_DIR}")
    print(f"📂 Directorio output: {OUTPUT_DIR}")
    print()
    
    # Verificar que existe el directorio de PDFs
    if not PDF_DIR.exists():
        print(f"❌ ERROR: No existe el directorio {PDF_DIR}")
        print(f"   Crear carpeta y colocar PDFs allí")
        return 1
    
    # Procesar
    processor = ChinfieldPDFProcessor(
        pdf_dir=str(PDF_DIR),
        output_dir=str(OUTPUT_DIR)
    )
    
    processed = processor.process_all_pdfs()
    
    if len(processed) > 0:
        print("\n✅ Proceso completado exitosamente")
        print(f"   {len(processed)} productos listos para indexar")
        return 0
    else:
        print("\n❌ No se pudo procesar ningún PDF")
        return 1


if __name__ == "__main__":
    exit(main())