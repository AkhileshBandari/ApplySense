from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import CareerPath, CareerPathScenario, ScenarioAssumption
from .serializers import CareerPathSerializer, CareerPathScenarioSerializer, ScenarioAssumptionSerializer
from .services import CareerPathRecommendationService, ScenarioSimulationEngine, PathwayRoadmapService

class CareerPathViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CareerPathSerializer

    def get_queryset(self):
        return CareerPath.objects.filter(active=True)

class CareerPathRecommendationView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        recommendations = CareerPathRecommendationService.evaluate_paths_for_user(request.user)
        return Response(recommendations)

class CareerPathScenarioViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CareerPathScenarioSerializer

    def get_queryset(self):
        return CareerPathScenario.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # We intercept create to use the service which handles baselining properly
        target_path_id = self.request.data.get('target_path_id')
        scenario = ScenarioSimulationEngine.create_scenario(
            user=self.request.user,
            name=serializer.validated_data.get('name'),
            target_path_id=target_path_id,
            overrides={
                'target_role': serializer.validated_data.get('target_role', ''),
                'target_country': serializer.validated_data.get('target_country', '')
            }
        )
        return scenario

    def create(self, request, *args, **kwargs):
        # Override to return our service-created instance
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scenario = self.perform_create(serializer)
        
        # Add any initial assumptions provided in the payload
        assumptions_data = request.data.get('assumptions', [])
        for a_data in assumptions_data:
            ScenarioAssumption.objects.create(
                scenario=scenario,
                assumption_type=a_data.get('assumption_type'),
                structured_data=a_data.get('structured_data', {})
            )
            
        resp_serializer = self.get_serializer(scenario)
        return Response(resp_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def simulate(self, request, pk=None):
        scenario = self.get_object()
        
        # Add new assumptions if provided
        new_assumptions = request.data.get('assumptions', [])
        for a_data in new_assumptions:
            ScenarioAssumption.objects.create(
                scenario=scenario,
                assumption_type=a_data.get('assumption_type'),
                structured_data=a_data.get('structured_data', {})
            )
            
        delta = ScenarioSimulationEngine.simulate(scenario)
        
        # Optional: Generate roadmap for simulation
        stages = PathwayRoadmapService.generate_stages(scenario.simulated_snapshot, scenario.target_path)
        
        serializer = self.get_serializer(scenario)
        return Response({
            "scenario": serializer.data,
            "delta": delta,
            "simulated_roadmap_stages": stages
        })

    @action(detail=True, methods=['get'])
    def comparison(self, request, pk=None):
        scenario = self.get_object()
        
        # Just return delta/diff without mutating
        delta = ScenarioSimulationEngine.calculate_delta(scenario)
        stages = PathwayRoadmapService.generate_stages(scenario.simulated_snapshot, scenario.target_path)
        
        return Response({
            "baseline": scenario.baseline_snapshot,
            "simulated": scenario.simulated_snapshot,
            "delta": delta,
            "simulated_roadmap_stages": stages
        })
