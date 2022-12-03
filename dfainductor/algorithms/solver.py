from typing import List, Iterable, Set
from subprocess import run, PIPE
from tempfile import TemporaryDirectory
import os.path as path_util
from ..logging_utils import log_info


class Solver:
    data_file_name = "cnf_data.txt"
    model_file_name = "cnf_model.txt"
    def __init__(self, solver_path: str, number_cores: int):
        self._solver_path = solver_path
        self._number_cores = number_cores
        self.clauses: List[List[int]] = []
        self.model: List[bool] = []
        self.vars: Set[int] = set()

    def solve(self, assumptions: Iterable[Iterable[int]]) -> bool:
        if assumptions:
            raise NotImplemented(f"Assumptions are not implemented")

        self.model = []

        with TemporaryDirectory() as dir:
            full_path_in = path_util.join(dir, Solver.data_file_name)
            full_path_out = path_util.join(dir, Solver.model_file_name)
            self.__generate_cnf(full_path_in)            
            res = run([
                    self._solver_path,
                    '-no-luby',
                    '-rinc=1.5',
                    '-phase-saving=0',
                    '-rnd-freq=0.02',
                    f'-ncores={self._number_cores}',
                    '-limitEx=10',
                    '-det=0',
                    '-ctrl=0',                    
                    f'{full_path_in}',
                    f'{full_path_out}'
            ], stdout=PIPE, stderr=PIPE, text=True)            
        
            if res.stdout and "UNSATISFIABLE" in res.stdout:                
                return False
            elif res.stdout and "SATISFIABLE" in res.stdout:
                return self.__parse_cnf(full_path_out)
            else:
                log_info(f'Error when executing SAT (return code {res.returncode}):\n{res.stdout or "No stdout!"}\n=================\n{res.stderr or "No stderr"}')                
        
        return False

    def nof_vars(self) -> int:
        return len(self.vars)

    def nof_clauses(self) -> int:
        return len(self.clauses)

    def get_model(self) -> List[bool]:
        return self.model

    def append_formula(self, clauses: Iterable[Iterable[int]]):
        [self.add_clause(c) for c in clauses]

    def add_clause(self, clause: Iterable[int]):
        [self.vars.add(abs(x)) for x in clause]
        self.clauses.append(list(clause))
    
    def __generate_cnf(self, file_path: str):
        with open(file_path, 'w+') as f:
            f.write(f'p cnf {len(self.vars)} {len(self.clauses)}')
            f.write("\n")
            f.writelines([f'{" ".join(str(v) for v in vars)} 0\n' for vars in self.clauses])

    def __parse_cnf(self, full_path: str):
        if path_util.exists(full_path):
            with open(full_path, 'r') as f:
                lines: List[str] = f.readlines()
                for l in lines:
                    if l.startswith('c') or l.startswith("SAT"):
                        continue

                    vars = [int(v) for v in l.split(' ') if v != '0']
                    self.model = [False if v < 0 else True for v in vars]                        
                    return True

        return False


